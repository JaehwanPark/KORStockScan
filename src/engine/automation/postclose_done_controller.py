"""Recover postclose automation into a final DONE/pass state when safe."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PROJECT_ROOT / "data" / "report"
OUTPUT_DIR = REPORT_DIR / "postclose_done_controller"
PYTHON_CANDIDATES = (
    PROJECT_ROOT / ".venv" / "bin" / "python",
    PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
    PROJECT_ROOT / "venv" / "bin" / "python",
    PROJECT_ROOT / "venv" / "Scripts" / "python.exe",
)

CommandRunner = Callable[[list[str], dict[str, str] | None], int]

NON_RECOVERABLE_TERMS = {
    "safety",
    "severe_loss",
    "real_runtime",
    "real-order",
    "real_order",
    "provider",
    "broker",
    "cap_release",
    "hard_safety",
    "auth_unavailable",
    "package_missing",
}
DONE_ACCEPTABLE_WARNING_ISSUES = {
    "active_sim_priority_preopen_handoff_pending",
}


@dataclass(frozen=True)
class RecoveryAction:
    action: str
    command: list[str] | None
    reason: str


def _python_bin() -> str:
    for candidate in PYTHON_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return "python"


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _run_command(command: list[str], env: dict[str, str] | None = None) -> int:
    merged_env = None
    if env:
        import os

        merged_env = os.environ.copy()
        merged_env.update(env)
    return subprocess.run(command, cwd=PROJECT_ROOT, env=merged_env, check=False).returncode


def _action_env(action: RecoveryAction) -> dict[str, str]:
    env = {"PYTHONPATH": "."}
    if action.action == "rerun_threshold_cycle_postclose":
        env["THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION"] = "stop"
    return env


def _verification_path(target_date: str) -> Path:
    return REPORT_DIR / "threshold_cycle_postclose_verification" / f"threshold_cycle_postclose_verification_{target_date}.json"


def _status_path(target_date: str) -> Path:
    return REPORT_DIR / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target_date}.status.json"


def _runtime_gap_path(target_date: str) -> Path:
    return REPORT_DIR / "runtime_apply_gap_audit" / f"runtime_apply_gap_audit_{target_date}.json"


def _workorder_path(target_date: str) -> Path:
    return REPORT_DIR / "code_improvement_workorder" / f"code_improvement_workorder_{target_date}.json"


def _runner_path(target_date: str) -> Path:
    return REPORT_DIR / "codex_workorder_runner" / f"codex_workorder_runner_{target_date}.json"


def _control_paths(target_date: str) -> tuple[Path, Path]:
    base = OUTPUT_DIR / f"postclose_done_controller_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _predecessor_wait_state(target_date: str) -> str | None:
    status_file = _status_path(target_date)
    if not status_file.exists():
        return "predecessor_status_missing"
    predecessor_status = str(_load_json(status_file).get("status") or "")
    if predecessor_status in {"running", "started", "in_progress"}:
        return "predecessor_running"
    return None


def _flatten_issues(verification: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    predecessor = verification.get("predecessor_integrity")
    if isinstance(predecessor, dict):
        issues.extend(str(item) for item in predecessor.get("log_issues") or [] if str(item))
        issues.extend(str(item) for item in predecessor.get("timeouts") or [] if str(item))
    for key in (
        "missing_required_artifacts",
        "missing_downstream_links",
        "stale_downstream_links",
        "source_generation_warnings",
        "handoff_warnings",
    ):
        issues.extend(str(item) for item in verification.get(key) or [] if str(item))
    runtime_gap = verification.get("runtime_apply_gap_audit")
    if isinstance(runtime_gap, dict):
        issues.extend(str(item) for item in runtime_gap.get("issues") or [] if str(item))
    for section in (
        "entry_bucket_handoff",
        "submit_bucket_handoff",
        "holding_bucket_handoff",
        "exit_bucket_handoff",
        "scale_in_bucket_handoff",
        "overnight_bucket_handoff",
        "lifecycle_bucket_discovery_handoff",
        "swing_lifecycle_handoff",
        "producer_gap_discovery_handoff",
        "stage_hook_workorder_handoff",
    ):
        value = verification.get(section)
        if isinstance(value, dict) and value.get("status") == "fail":
            issues.extend(str(item) for item in value.get("missing") or [] if str(item))
    return list(dict.fromkeys(issues))


def _has_non_recoverable_issue(issues: list[str]) -> bool:
    joined = " ".join(issues).lower()
    return any(term in joined for term in NON_RECOVERABLE_TERMS)


def _has_done_marker(verification: dict[str, Any]) -> bool:
    marker = str(verification.get("latest_done_marker") or "").strip()
    return bool(marker and marker != "-")


def _postclose_status_succeeded(target_date: str) -> bool:
    return str(_load_json(_status_path(target_date)).get("status") or "") == "succeeded"


def _is_done_verifier_status(target_date: str, verification: dict[str, Any], issues: list[str]) -> bool:
    verifier_status = str(verification.get("status") or "")
    if verifier_status == "pass":
        return True
    if verifier_status != "warning":
        return False
    if not _has_done_marker(verification) or not _postclose_status_succeeded(target_date):
        return False
    return set(issues).issubset(DONE_ACCEPTABLE_WARNING_ISSUES)


def _runner_completed(runner_report: dict[str, Any], *, dry_run: bool = False) -> bool:
    runner_status = str(runner_report.get("status") or "missing")
    two_pass_status = str(runner_report.get("two_pass_status") or "missing")
    if dry_run:
        return runner_status == "dry_run_planned"
    return runner_status == "completed" and two_pass_status in {"pass2_completed", "pass2_not_required", "not_required"}


def _build_verify_action(target_date: str) -> RecoveryAction:
    return RecoveryAction(
        "verify_postclose_chain",
        [_python_bin(), "-m", "src.engine.verify_threshold_cycle_postclose_chain", "--date", target_date],
        "refresh verifier status",
    )


def _build_codex_runner_action(target_date: str) -> RecoveryAction:
    return RecoveryAction(
        "run_codex_workorder_runner",
        [_python_bin(), "-m", "src.engine.automation.codex_workorder_runner", "--date", target_date],
        "codex workorder runner strict completion or 2-pass incomplete",
    )


def _recovery_actions(target_date: str, verification: dict[str, Any], *, allow_wrapper_rerun: bool) -> list[RecoveryAction]:
    issues = _flatten_issues(verification)
    actions: list[RecoveryAction] = []
    issue_text = " ".join(issues)
    log_issues = (
        ((verification.get("predecessor_integrity") or {}).get("log_issues") or [])
        if isinstance(verification.get("predecessor_integrity"), dict)
        else []
    )
    if allow_wrapper_rerun and any(
        item in {"postclose_start_marker_missing", "postclose_done_marker_missing", "postclose_fail_marker_present"}
        for item in log_issues
    ):
        actions.append(
            RecoveryAction(
                "rerun_threshold_cycle_postclose",
                ["bash", "deploy/run_threshold_cycle_postclose.sh", target_date],
                "wrapper marker missing",
            )
        )
        return actions
    if "runtime_apply_gap" in issue_text:
        actions.append(
            RecoveryAction(
                "refresh_runtime_apply_gap_audit",
                [_python_bin(), "-m", "src.engine.runtime_apply_gap_audit", "--date", target_date],
                "runtime apply gap audit issue",
            )
        )
    if "code_improvement_workorder" in issue_text or not _workorder_path(target_date).exists():
        actions.append(
            RecoveryAction(
                "refresh_code_improvement_workorder",
                [_python_bin(), "-m", "src.engine.build_code_improvement_workorder", "--date", target_date],
                "workorder source or lineage issue",
            )
        )
    if (
        verification.get("missing_downstream_links")
        or verification.get("stale_downstream_links")
        or verification.get("source_generation_warnings")
        or verification.get("missing_required_artifacts")
    ):
        actions.extend(
            [
                RecoveryAction(
                    "refresh_threshold_cycle_ev",
                    [_python_bin(), "-m", "src.engine.threshold_cycle_ev_report", "--date", target_date],
                    "downstream EV source refresh",
                ),
                RecoveryAction(
                    "refresh_runtime_approval_summary",
                    [_python_bin(), "-m", "src.engine.runtime_approval_summary", "--date", target_date],
                    "runtime summary source refresh",
                ),
            ]
        )
    return actions


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Postclose DONE Controller - {report.get('date')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- final_verifier_status: `{report.get('final_verifier_status')}`",
        f"- attempts: `{len(report.get('attempts') or [])}`",
        f"- dry_run: `{report.get('dry_run')}`",
        "",
        "## Actions",
    ]
    for item in report.get("actions") or []:
        lines.append(
            f"- `{item.get('action')}` status=`{item.get('status')}` reason=`{item.get('reason')}`"
        )
    if not report.get("actions"):
        lines.append("- none")
    blocked = report.get("blocked_reasons") or []
    if blocked:
        lines.extend(["", "## Blocked Reasons"])
        lines.extend(f"- `{item}`" for item in blocked)
    lines.append("")
    return "\n".join(lines)


def build_postclose_done_controller(
    target_date: str,
    *,
    max_attempts: int = 3,
    predecessor_wait_sec: float = 60.0,
    predecessor_timeout_sec: float = 14400.0,
    allow_wrapper_rerun: bool = False,
    require_codex_completed: bool = False,
    dry_run: bool = False,
    command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    command_runner = command_runner or _run_command
    attempts: list[dict[str, Any]] = []
    actions_done: list[dict[str, Any]] = []
    blocked_reasons: list[str] = []
    final_verifier: dict[str, Any] = {}
    predecessor_started_at = time.monotonic()

    recovery_attempt = 0
    while recovery_attempt < max(1, int(max_attempts)):
        wait_state = _predecessor_wait_state(target_date)
        if wait_state:
            elapsed_sec = time.monotonic() - predecessor_started_at
            attempts.append(
                {
                    "attempt": len(attempts) + 1,
                    "verify_exit_code": None,
                    "verifier_status": wait_state,
                    "predecessor_wait_elapsed_sec": round(elapsed_sec, 3),
                    "issue_count": 0,
                    "issues": [],
                }
            )
            if dry_run:
                blocked_reasons = [wait_state]
                break
            if elapsed_sec < predecessor_timeout_sec:
                time.sleep(predecessor_wait_sec)
                continue
            blocked_reasons = [f"{wait_state}_timeout"]
            break
        recovery_attempt += 1
        attempt = recovery_attempt
        verify_action = _build_verify_action(target_date)
        verify_rc = 0 if dry_run else command_runner(verify_action.command or [], {"PYTHONPATH": "."})
        final_verifier = _load_json(_verification_path(target_date))
        verifier_status = str(final_verifier.get("status") or "missing")
        issues = _flatten_issues(final_verifier)
        attempts.append(
            {
                "attempt": attempt,
                "verify_exit_code": verify_rc,
                "verifier_status": verifier_status,
                "issue_count": len(issues),
                "issues": issues,
            }
        )
        if _is_done_verifier_status(target_date, final_verifier, issues):
            if require_codex_completed and not dry_run:
                runner_report = _load_json(_runner_path(target_date))
                if not _runner_completed(runner_report, dry_run=dry_run):
                    action = _build_codex_runner_action(target_date)
                    rc = command_runner(action.command or [], _action_env(action))
                    actions_done.append(
                        {
                            "attempt": attempt,
                            "action": action.action,
                            "reason": action.reason,
                            "command": action.command,
                            "status": "success" if rc == 0 else "failed",
                            "exit_code": rc,
                        }
                    )
                    if rc != 0:
                        blocked_reasons.append(f"{action.action}_failed")
                        break
                    continue
            break
        if _has_non_recoverable_issue(issues):
            blocked_reasons = issues or [f"verifier_status={verifier_status}"]
            break
        actions = _recovery_actions(target_date, final_verifier, allow_wrapper_rerun=allow_wrapper_rerun)
        if not actions:
            blocked_reasons = issues or [f"verifier_status={verifier_status}"]
            break
        for action in actions:
            rc = 0 if dry_run else command_runner(action.command or [], _action_env(action))
            actions_done.append(
                {
                    "attempt": attempt,
                    "action": action.action,
                    "reason": action.reason,
                    "command": action.command,
                    "status": "planned" if dry_run else ("success" if rc == 0 else "failed"),
                    "exit_code": rc,
                }
            )
            if rc != 0 and not dry_run:
                blocked_reasons.append(f"{action.action}_failed")
                break
        if blocked_reasons:
            break

    final_status = str(final_verifier.get("status") or "missing")
    final_issues = _flatten_issues(final_verifier)
    runner_report = _load_json(_runner_path(target_date))
    runner_status = str(runner_report.get("status") or "missing")
    runner_two_pass_status = str(runner_report.get("two_pass_status") or "missing")
    runner_completed = _runner_completed(runner_report, dry_run=dry_run)
    if require_codex_completed and not dry_run and not runner_completed:
        blocked_reasons = list(dict.fromkeys([*blocked_reasons, f"codex_workorder_runner_not_completed:{runner_status}:{runner_two_pass_status}"]))

    if _is_done_verifier_status(target_date, final_verifier, final_issues) and not (
        require_codex_completed and not dry_run and not runner_completed
    ):
        status = "done"
    elif dry_run and (actions_done or blocked_reasons in (["predecessor_running"], ["predecessor_status_missing"])):
        status = "dry_run_planned"
    elif require_codex_completed and not dry_run and not runner_completed:
        status = "blocked_uncompleted_implementation"
    elif blocked_reasons and _has_non_recoverable_issue(blocked_reasons):
        status = "blocked_non_recoverable"
    elif any(str(reason).startswith("verifier_status=") for reason in blocked_reasons):
        status = "blocked_unclassified_verifier_status"
    elif blocked_reasons:
        status = "blocked_recoverable_action_failed"
    else:
        status = "exhausted_recoverable_actions"

    report = {
        "schema_version": 1,
        "report_type": "postclose_done_controller",
        "date": target_date,
        "generated_at": _now(),
        "status": status,
        "dry_run": dry_run,
        "allow_wrapper_rerun": allow_wrapper_rerun,
        "require_codex_completed": require_codex_completed,
        "max_attempts": max_attempts,
        "predecessor_wait_sec": predecessor_wait_sec,
        "predecessor_timeout_sec": predecessor_timeout_sec,
        "final_verifier_status": final_status,
        "threshold_cycle_postclose_status": _load_json(_status_path(target_date)).get("status"),
        "runtime_apply_gap_status": _load_json(_runtime_gap_path(target_date)).get("status"),
        "workorder_generation_id": _load_json(_workorder_path(target_date)).get("generation_id"),
        "codex_workorder_runner_status": runner_status,
        "codex_workorder_runner_two_pass_status": runner_two_pass_status,
        "codex_workorder_runner_completed": runner_completed,
        "attempts": attempts,
        "actions": actions_done,
        "blocked_reasons": blocked_reasons,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": [
            "real_order_authority",
            "provider_route_change",
            "bot_restart_authority",
            "broker_guard_relaxation",
            "hard_safety_relaxation",
        ],
    }
    json_path, md_path = _control_paths(target_date)
    _write_json(json_path, report)
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument(
        "--predecessor-wait-sec",
        type=float,
        default=float(os.environ.get("POSTCLOSE_DONE_CONTROLLER_PREDECESSOR_WAIT_SEC", "60")),
    )
    parser.add_argument(
        "--predecessor-timeout-sec",
        type=float,
        default=float(os.environ.get("POSTCLOSE_DONE_CONTROLLER_PREDECESSOR_TIMEOUT_SEC", "14400")),
    )
    parser.add_argument("--allow-wrapper-rerun", action="store_true")
    parser.add_argument(
        "--require-codex-completed",
        action="store_true",
        default=os.environ.get("POSTCLOSE_DONE_CONTROLLER_REQUIRE_CODEX_COMPLETED", "true").strip().lower()
        in {"1", "true", "yes", "on"},
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    report = build_postclose_done_controller(
        args.date,
        max_attempts=args.max_attempts,
        predecessor_wait_sec=args.predecessor_wait_sec,
        predecessor_timeout_sec=args.predecessor_timeout_sec,
        allow_wrapper_rerun=args.allow_wrapper_rerun,
        require_codex_completed=args.require_codex_completed,
        dry_run=args.dry_run,
    )
    print(json.dumps({"status": report["status"], "date": report["date"]}, ensure_ascii=False))
    return 0 if report["status"] in {"done", "dry_run_planned"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
