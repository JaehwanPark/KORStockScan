"""Close postclose work by rebuilding direct summaries and strict verification."""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.build_next_stage2_checklist import build_next_stage2_checklist
from src.engine.runtime_approval_summary import build_runtime_approval_summary
from src.engine.verify_threshold_cycle_postclose_chain import (
    build_threshold_cycle_postclose_verification,
    _write_verification_receipts,
    _atomic_write,
)
from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report" / "postclose_done_controller"


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _status_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target_date}.status.json"


def _control_paths(target_date: str) -> tuple[Path, Path]:
    return (
        REPORT_DIR / f"postclose_done_controller_{target_date}.json",
        REPORT_DIR / f"postclose_done_controller_{target_date}.md",
    )


def _wait_for_predecessor_succeeded(
    target_date: str, *, wait_sec: float, timeout_sec: float
) -> bool:
    """Wait for the exact-date main postclose terminal without rerunning it."""
    interval = max(0.1, float(wait_sec))
    deadline = time.monotonic() + max(0.0, float(timeout_sec))
    while True:
        if _load(_status_path(target_date)).get("status") == "succeeded":
            return True
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(interval, remaining))


def build_postclose_done_controller(
    target_date: str,
    *,
    max_attempts: int = 3,
    predecessor_wait_sec: float = 60,
    predecessor_timeout_sec: float = 43200,
    allow_wrapper_rerun: bool = False,
    require_codex_completed: bool = False,
    dry_run: bool = False,
    summary_handoff_only: bool = False,
    require_independent_producers: bool = False,
) -> dict[str, Any]:
    date.fromisoformat(target_date)
    predecessor = _load(_status_path(target_date))
    actions: list[str] = []
    independent_issues = []
    if require_independent_producers:
        from src.engine.automation.postclose_summary_handoff import producer_receipt_issues
        for owner in ("widget", "machine"):
            independent_issues.extend(producer_receipt_issues(DATA_DIR / "report", target_date, owner))
    if dry_run:
        status = "dry_run_planned"
        verifier = {"status": "not_run", "issues": []}
    elif predecessor.get("status") != "succeeded" and not summary_handoff_only:
        status = "blocked_predecessor_not_succeeded"
        verifier = {"status": "not_run", "issues": ["postclose_terminal_status_missing"]}
    elif independent_issues:
        status = "blocked_independent_producer"
        verifier = {"status": "not_run", "issues": independent_issues}
    else:
        build_runtime_approval_summary(target_date)
        actions.append("runtime_approval_summary_refreshed")
        build_next_stage2_checklist(target_date)
        actions.append("next_stage2_checklist_refreshed")
        verifier = build_threshold_cycle_postclose_verification(
            target_date,
            require_done_marker=not summary_handoff_only,
            require_summary_handoff=True,
        )
        verifier, *_ = _write_verification_receipts(
            target_date,
            verifier,
            invocation={
                "controller": True,
                "summary_handoff_only": summary_handoff_only,
                "require_done_marker": not summary_handoff_only,
            },
        )
        actions.append("direct_postclose_verification_refreshed")
        status = ("summary_verified" if summary_handoff_only else "done") if verifier.get("status") == "pass" else "blocked_direct_evidence_gap"
    from src.engine.automation.postclose_summary_handoff import STAGE_REGISTRY, stage_path, stage_overview
    stage_state = None
    if any(stage_path(DATA_DIR / 'report', target_date, stage).exists() for stage in STAGE_REGISTRY):
        stage_state = stage_overview(DATA_DIR / 'report', target_date)
        if status == 'summary_verified' and predecessor.get('status') == 'succeeded' and require_independent_producers:
            status = 'done'
        stage_state['postclose_all_active_stages_complete'] = require_independent_producers and not independent_issues and verifier.get('status') == 'pass' and status == 'done'
    report = {
        "postclose_stage_status": stage_state,
        "schema_version": 2,
        "report_type": "postclose_done_controller",
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "dry_run": dry_run,
        "summary_handoff_only": summary_handoff_only,
        "whole_native_chain_done_claimed": status == "done" and require_independent_producers,
        "require_independent_producers": require_independent_producers,
        "wait_owner": "calling_wrapper",
        "allow_wrapper_rerun": allow_wrapper_rerun,
        "full_wrapper_rerun_used": False,
        "common_tuning_recovery_retired": True,
        "final_verifier_status": verifier.get("status"),
        "blocked_reasons": list(verifier.get("issues") or []),
        "actions": actions,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "require_codex_completed": require_codex_completed,
        "max_attempts": max_attempts,
        "predecessor_wait_sec": predecessor_wait_sec,
        "predecessor_timeout_sec": predecessor_timeout_sec,
    }
    json_path, md_path = _control_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    attempt = json_path.parent / "attempts" / f"{target_date}_{uuid.uuid4().hex}.json"
    report["attempt_path"] = str(attempt)
    report["main_run_id"] = predecessor.get("run_id")
    report["verification_attempt_path"] = (verifier.get("verification_attempt") or {}).get("path")
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    _atomic_write(attempt, serialized)
    _atomic_write(json_path, serialized)
    _atomic_write(md_path,
        "\n".join([
            f"# Postclose done controller - {target_date}", "",
            f"- status: `{status}`",
            f"- verifier: `{verifier.get('status')}`",
            "- recovery owner: direct family evidence and summary only",
            "- common Daily/EV rerun: `retired`",
            f"- blockers: `{report['blocked_reasons']}`", "",
        ]),
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--predecessor-wait-sec", type=float, default=float(os.environ.get("POSTCLOSE_DONE_CONTROLLER_PREDECESSOR_WAIT_SEC", "60")))
    parser.add_argument("--predecessor-timeout-sec", type=float, default=float(os.environ.get("POSTCLOSE_DONE_CONTROLLER_PREDECESSOR_TIMEOUT_SEC", "43200")))
    parser.add_argument("--allow-wrapper-rerun", action="store_true")
    parser.add_argument("--summary-handoff-only", action="store_true")
    parser.add_argument("--require-independent-producers", action="store_true")
    parser.add_argument("--require-codex-completed", action="store_true", default=False)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    from src.engine.automation.postclose_summary_handoff import STAGE_REGISTRY, stage_path, _stage_main
    if not args.dry_run and os.environ.get('POSTCLOSE_STAGE_WORKER') != '1' and any(stage_path(DATA_DIR / 'report', args.date, s).exists() for s in STAGE_REGISTRY):
        return _stage_main(['--stage', 'summary_handoff', '--date', args.date])
    if not args.dry_run and not args.summary_handoff_only:
        _wait_for_predecessor_succeeded(
            args.date,
            wait_sec=args.predecessor_wait_sec,
            timeout_sec=args.predecessor_timeout_sec,
        )
    report = build_postclose_done_controller(
        args.date,
        max_attempts=args.max_attempts,
        predecessor_wait_sec=args.predecessor_wait_sec,
        predecessor_timeout_sec=args.predecessor_timeout_sec,
        allow_wrapper_rerun=args.allow_wrapper_rerun,
        require_codex_completed=args.require_codex_completed,
        dry_run=args.dry_run,
        summary_handoff_only=args.summary_handoff_only,
        require_independent_producers=args.require_independent_producers,
    )
    print(json.dumps({"status": report["status"], "date": report["date"]}, ensure_ascii=False))
    return 0 if report["status"] in {"done", "summary_verified", "dry_run_planned"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
