"""Run safe code-improvement workorders through the Codex Python SDK."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import threading
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PROJECT_ROOT / "data" / "report"
WORKORDER_REPORT_DIR = REPORT_DIR / "code_improvement_workorder"
OUTPUT_DIR = REPORT_DIR / "codex_workorder_runner"
WORKTREE_ROOT = PROJECT_ROOT / "tmp" / "codex_worktrees"
PYTHON_CANDIDATES = (
    PROJECT_ROOT / ".venv" / "bin" / "python",
    PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
    PROJECT_ROOT / "venv" / "bin" / "python",
    PROJECT_ROOT / "venv" / "Scripts" / "python.exe",
)

CommandRunner = Callable[[list[str], Path | None], int]
CaptureRunner = Callable[[list[str], Path | None], tuple[int, str]]

ALLOWED_AUTO_COMMIT_PATH_PREFIXES = (
    "docs/",
    "src/tests/",
    "src/engine/automation/",
    "src/engine/monitoring/",
    "src/engine/error_detectors/",
)
ALLOWED_AUTO_COMMIT_EXACT_PATHS = {
    "requirements.txt",
}
FORBIDDEN_USE_TERMS = {
    "real_order",
    "broker",
    "provider",
    "bot_restart",
    "cap_release",
    "hard_safety",
    "emergency",
    "protect_stop",
    "threshold_runtime_env",
    "preopen live env",
}

FORBIDDEN_DIFF_PATTERNS = {
    "broker_guard_relaxation",
    "broker guard relaxation",
    "provider_route_change",
    "provider route change",
    "real_order_authority",
    "real order authority",
    "bot_restart",
    "bot restart",
    "cap_release",
    "cap release",
    "hard_safety_relaxation",
    "hard safety relaxation",
    "hard_safety bypass",
    "hard safety bypass",
    "threshold_runtime_env",
    "preopen live env",
}
ALLOWED_ACCEPTANCE_COMMAND_PREFIXES = (
    "python -m pytest ",
    "pytest ",
    "python -m src.engine.sync_docs_backlog_to_project ",
    "python -m py_compile ",
)


@dataclass(frozen=True)
class CodexTurnSummary:
    phase: str
    final_response: str


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


def _run_command(command: list[str], cwd: Path | None = None) -> int:
    return subprocess.run(command, cwd=cwd or PROJECT_ROOT, check=False).returncode


def _run_capture(command: list[str], cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        cwd=cwd or PROJECT_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    return proc.returncode, proc.stdout


def _python_bin() -> str:
    for candidate in PYTHON_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return "python"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _wait_for_codex_login(login: Any, timeout_sec: float) -> str | None:
    result: dict[str, str] = {}

    def _wait() -> None:
        try:
            login.wait()
        except Exception as exc:
            result["error"] = f"codex_login_wait_failed:{exc.__class__.__name__}"

    thread = threading.Thread(target=_wait, daemon=True)
    thread.start()
    thread.join(max(0.0, timeout_sec))
    if thread.is_alive():
        return f"codex_login_timeout:{timeout_sec:g}s"
    return result.get("error")


def _workorder_path(target_date: str) -> Path:
    return WORKORDER_REPORT_DIR / f"code_improvement_workorder_{target_date}.json"


def _runner_paths(target_date: str) -> tuple[Path, Path]:
    base = OUTPUT_DIR / f"codex_workorder_runner_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _text_blob(order: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("order_id", "title", "target_subsystem", "lifecycle_stage", "threshold_family", "decision_reason"):
        values.append(str(order.get(key) or ""))
    for key in ("files_likely_touched", "acceptance_tests"):
        raw = order.get(key)
        if isinstance(raw, list):
            values.extend(str(item) for item in raw)
        else:
            values.append(str(raw or ""))
    return " ".join(values).lower()


def is_safe_implement_now(order: dict[str, Any]) -> bool:
    return _safe_implement_now_block_reason(order) is None


def _safe_implement_now_block_reason(order: dict[str, Any]) -> str | None:
    if str(order.get("decision") or "") != "implement_now":
        return "not_implement_now"
    if order.get("runtime_effect") is not False:
        return "runtime_effect_not_false"
    if order.get("allowed_runtime_apply") is True:
        return "allowed_runtime_apply_true"
    forbidden_uses = order.get("forbidden_uses")
    if not isinstance(forbidden_uses, list) or not any(str(item).strip() for item in forbidden_uses):
        return "missing_forbidden_uses_contract"
    blob = _text_blob(order)
    if any(term in blob for term in FORBIDDEN_USE_TERMS):
        return "forbidden_or_not_safe"
    return None


def triage_non_implement(order: dict[str, Any]) -> str:
    decision = str(order.get("decision") or "")
    status = str(order.get("implementation_status") or "")
    if status.startswith("implemented"):
        return "attached_to_existing_family"
    if decision == "attach_existing_family":
        return "needs_codex_instrumentation" if order.get("runtime_effect") is False else "stale_no_action"
    if decision == "design_family_candidate":
        return "design_backlog_required" if order.get("allowed_runtime_apply") is False else "merge_into_existing_family"
    if decision == "defer_evidence":
        repeat = order.get("repeat_unresolved") or order.get("repeat_count") or 0
        try:
            repeat_count = int(repeat)
        except Exception:
            repeat_count = 0
        return "promoted" if repeat_count >= 2 and order.get("runtime_effect") is False else "continue_defer"
    return "drop_stale" if decision == "reject" else "stale_no_action"


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Codex Workorder Runner - {report.get('date')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- implemented_order_count: `{len(report.get('implemented_orders') or [])}`",
        f"- blocked_order_count: `{len(report.get('blocked_orders') or [])}`",
        f"- dry_run: `{report.get('dry_run')}`",
        f"- worktree: `{report.get('worktree') or '-'}`",
        "",
        "## Implemented Orders",
    ]
    for item in report.get("implemented_orders") or []:
        lines.append(f"- `{item.get('order_id')}` status=`{item.get('status')}`")
    if not report.get("implemented_orders"):
        lines.append("- none")
    lines.extend(["", "## Non-Implement Triage"])
    for item in report.get("non_implement_triage") or []:
        lines.append(f"- `{item.get('order_id')}` decision=`{item.get('decision')}` triage=`{item.get('triage')}`")
    if not report.get("non_implement_triage"):
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _make_worktree(
    target_date: str,
    branch_prefix: str,
    command_runner: CommandRunner,
    dry_run: bool,
    capture_runner: CaptureRunner | None = None,
) -> tuple[Path, str, int, str]:
    branch = f"{branch_prefix.rstrip('/')}-{target_date}"
    worktree = WORKTREE_ROOT / branch
    if dry_run:
        return worktree, branch, 0, "planned"
    if worktree.exists():
        if not (worktree / ".git").exists():
            return worktree, branch, 2, "worktree_path_exists_not_git"
        capture_runner = capture_runner or _run_capture
        status_rc, status_stdout = capture_runner(["git", "status", "--porcelain"], worktree)
        if status_rc != 0:
            return worktree, branch, status_rc, "worktree_status_failed"
        if status_stdout.strip():
            return worktree, branch, 2, "worktree_dirty"
        root_rc, root_head = capture_runner(["git", "rev-parse", "HEAD"], PROJECT_ROOT)
        tree_rc, tree_head = capture_runner(["git", "rev-parse", "HEAD"], worktree)
        if root_rc != 0 or tree_rc != 0:
            return worktree, branch, 2, "worktree_head_check_failed"
        if root_head.strip() != tree_head.strip():
            return worktree, branch, 2, "worktree_stale_head"
        return worktree, branch, 0, "reused_clean_worktree"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    rc = command_runner(["git", "worktree", "add", "-B", branch, str(worktree), "HEAD"], PROJECT_ROOT)
    return worktree, branch, rc, "created" if rc == 0 else "worktree_add_failed"


def _codex_turns(worktree: Path, orders: list[dict[str, Any]], dry_run: bool) -> tuple[list[CodexTurnSummary], str | None]:
    if dry_run or not orders:
        return [], None
    try:
        from openai_codex import Codex, Sandbox
    except Exception as exc:
        return [], f"openai_codex_unavailable:{exc.__class__.__name__}"
    prompt = (
        "Implement the provided KORStockScan code-improvement workorders. "
        "Only change runtime_effect=false source-quality, parser/schema, report, test, documentation, "
        "instrumentation, or sim/source-only code. Do not change real order authority, provider route, "
        "bot state, caps, broker/order guards, hard/protect/emergency safety, or PREOPEN live env authority.\n\n"
        + json.dumps({"orders": orders}, ensure_ascii=False, indent=2)
    )
    turns: list[CodexTurnSummary] = []
    with Codex() as codex:
        try:
            codex.account(refresh_token=False)
        except Exception:
            login = codex.login_chatgpt_device_code()
            verification_url = str(getattr(login, "verification_url", "") or "")
            user_code = str(getattr(login, "user_code", "") or "")
            print(verification_url)
            print(user_code)
            if not _env_bool("CODEX_WORKORDER_ALLOW_INTERACTIVE_LOGIN", False):
                return turns, "codex_login_required"
            login_error = _wait_for_codex_login(
                login,
                float(os.environ.get("CODEX_WORKORDER_LOGIN_WAIT_TIMEOUT_SEC", "900")),
            )
            if login_error:
                return turns, login_error
        thread = codex.thread_start(cwd=str(worktree), sandbox=Sandbox.workspace_write)
        result = thread.run(prompt)
        turns.append(CodexTurnSummary("implement", str(getattr(result, "final_response", ""))))
        review = thread.run("Review the diff only. List blocking issues first.", sandbox=Sandbox.read_only)
        turns.append(CodexTurnSummary("review", str(getattr(review, "final_response", ""))))
        fix = thread.run("Fix any blocking issues found in the review, then summarize.", sandbox=Sandbox.workspace_write)
        turns.append(CodexTurnSummary("supplemental_fix", str(getattr(fix, "final_response", ""))))
        final_review = thread.run("Final read-only review of the resulting diff.", sandbox=Sandbox.read_only)
        turns.append(CodexTurnSummary("final_review", str(getattr(final_review, "final_response", ""))))
    return turns, None


def _run_validation(worktree: Path, command_runner: CommandRunner, dry_run: bool) -> list[dict[str, Any]]:
    commands = [
        ["git", "diff", "--check", "HEAD"],
        [_python_bin(), "-m", "pytest", "-q", "src/tests/test_build_code_improvement_workorder.py"],
        [_python_bin(), "-m", "pytest", "-q", "src/tests/test_verify_threshold_cycle_postclose_chain.py"],
        [_python_bin(), "-m", "src.engine.sync_docs_backlog_to_project", "--print-backlog-only", "--limit", "500"],
    ]
    results: list[dict[str, Any]] = []
    for command in commands:
        rc = 0 if dry_run else command_runner(command, worktree)
        results.append({"command": command, "exit_code": rc, "status": "planned" if dry_run else ("pass" if rc == 0 else "fail")})
        if rc != 0 and not dry_run:
            break
    return results


def _acceptance_commands(orders: list[dict[str, Any]]) -> tuple[list[list[str]], list[str]]:
    commands: list[list[str]] = []
    unsupported: list[str] = []
    for order in orders:
        for raw in order.get("acceptance_tests") or []:
            text = str(raw).strip()
            if not text:
                continue
            normalized = text
            if normalized.startswith("PYTHONPATH=. "):
                normalized = normalized[len("PYTHONPATH=. "):]
            if normalized.startswith(".venv/bin/python "):
                normalized = "python " + normalized[len(".venv/bin/python "):]
            if normalized.startswith("./.venv/bin/python "):
                normalized = "python " + normalized[len("./.venv/bin/python "):]
            if normalized.startswith("venv/Scripts/python.exe "):
                normalized = "python " + normalized[len("venv/Scripts/python.exe "):]
            if not any(normalized.startswith(prefix) for prefix in ALLOWED_ACCEPTANCE_COMMAND_PREFIXES):
                unsupported.append(text)
                continue
            parts = normalized.split()
            if parts[0] == "python":
                parts[0] = _python_bin()
            elif parts[0] == "pytest":
                parts = [_python_bin(), "-m", "pytest", *parts[1:]]
            commands.append(parts)
    return commands, unsupported


def _run_acceptance_tests(
    worktree: Path,
    orders: list[dict[str, Any]],
    command_runner: CommandRunner,
    dry_run: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    commands, unsupported = _acceptance_commands(orders)
    results: list[dict[str, Any]] = []
    for command in commands:
        rc = 0 if dry_run else command_runner(command, worktree)
        results.append({"command": command, "exit_code": rc, "status": "planned" if dry_run else ("pass" if rc == 0 else "fail")})
        if rc != 0 and not dry_run:
            break
    return results, unsupported


def _forbidden_diff_scan(
    worktree: Path,
    command_runner: CommandRunner,
    dry_run: bool,
    capture_runner: CaptureRunner | None = None,
) -> dict[str, Any]:
    if dry_run:
        return {"status": "planned", "matches": []}
    capture_runner = capture_runner or _run_capture
    name_rc, name_stdout = capture_runner(["git", "diff", "--name-only", "HEAD"], worktree)
    diff_rc, diff_stdout = capture_runner(["git", "diff", "HEAD", "--"], worktree)
    untracked_rc, untracked_stdout = capture_runner(["git", "ls-files", "--others", "--exclude-standard"], worktree)
    if name_rc != 0 or diff_rc != 0 or untracked_rc != 0:
        return {"status": "fail", "matches": ["git_diff_failed"]}
    untracked_files = [line.strip() for line in untracked_stdout.splitlines() if line.strip()]
    files = list(
        dict.fromkeys(
            [
                *[line.strip() for line in name_stdout.splitlines() if line.strip()],
                *untracked_files,
            ]
        )
    )
    disallowed_files = [
        path
        for path in files
        if path not in ALLOWED_AUTO_COMMIT_EXACT_PATHS
        and not any(path.startswith(prefix) for prefix in ALLOWED_AUTO_COMMIT_PATH_PREFIXES)
    ]
    forbidden_files = [
        path
        for path in files
        if any(token in path.lower() for token in ("runtime_env", "approvals", "kiwoom_orders", "run_bot.sh"))
    ]
    changed_lines = [
        line[1:].lower()
        for line in diff_stdout.splitlines()
        if (line.startswith("+") and not line.startswith("+++"))
        or (line.startswith("-") and not line.startswith("---"))
    ]
    for path in untracked_files:
        try:
            changed_lines.extend((worktree / path).read_text(encoding="utf-8", errors="replace").lower().splitlines())
        except OSError:
            changed_lines.append(f"unreadable_untracked:{path}")
    changed_text = "\n".join(changed_lines)
    forbidden_terms = sorted(term for term in FORBIDDEN_DIFF_PATTERNS if term in changed_text)
    matches = [
        *[f"disallowed_path:{path}" for path in disallowed_files],
        *forbidden_files,
        *[f"diff_term:{term}" for term in forbidden_terms],
    ]
    return {"status": "fail" if matches else "pass", "matches": matches}


def _codex_error_status(codex_error: str) -> str:
    if codex_error.startswith("openai_codex_unavailable"):
        return "codex_package_unavailable"
    if codex_error.startswith("codex_login_required"):
        return "codex_login_required"
    if codex_error.startswith("codex_login_timeout"):
        return "codex_login_timeout"
    return "codex_unavailable"


def build_codex_workorder_runner(
    target_date: str,
    *,
    max_orders: int = 5,
    branch_prefix: str = "codex-workorder",
    commit: bool = False,
    dry_run: bool = False,
    command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    command_runner = command_runner or _run_command
    workorder = _load_json(_workorder_path(target_date))
    orders = [item for item in workorder.get("orders") or [] if isinstance(item, dict)]
    safe_orders = [item for item in orders if is_safe_implement_now(item)][: max(0, int(max_orders))]
    blocked_orders = []
    for item in orders:
        if str(item.get("decision") or "") != "implement_now" or item in safe_orders:
            continue
        blocked_orders.append(
            {
                "order_id": item.get("order_id"),
                "decision": item.get("decision"),
                "reason": _safe_implement_now_block_reason(item) or "forbidden_or_not_safe",
            }
        )
    non_implement_triage = [
        {
            "order_id": item.get("order_id"),
            "decision": item.get("decision"),
            "triage": triage_non_implement(item),
            "runtime_effect": item.get("runtime_effect"),
        }
        for item in [*orders, *(workorder.get("non_selected_orders") or [])]
        if isinstance(item, dict) and str(item.get("decision") or "") != "implement_now"
    ]
    worktree, branch, worktree_rc, worktree_status = _make_worktree(target_date, branch_prefix, command_runner, dry_run)
    codex_turns: list[CodexTurnSummary] = []
    codex_error: str | None = None
    validation_results: list[dict[str, Any]] = []
    acceptance_results: list[dict[str, Any]] = []
    unsupported_acceptance_tests: list[str] = []
    forbidden_scan = {"status": "not_run", "matches": []}
    commit_rc: int | None = None
    if worktree_rc == 0 and safe_orders:
        codex_turns, codex_error = _codex_turns(worktree, safe_orders, dry_run)
        if not codex_error:
            validation_results = _run_validation(worktree, command_runner, dry_run)
            validations_pass = all(item["exit_code"] == 0 for item in validation_results)
            if validations_pass:
                acceptance_results, unsupported_acceptance_tests = _run_acceptance_tests(
                    worktree,
                    safe_orders,
                    command_runner,
                    dry_run,
                )
            acceptance_pass = (
                validations_pass
                and not unsupported_acceptance_tests
                and all(item["exit_code"] == 0 for item in acceptance_results)
            )
            if acceptance_pass:
                forbidden_scan = _forbidden_diff_scan(worktree, command_runner, dry_run)
            if commit and acceptance_pass and forbidden_scan["status"] != "fail":
                add_rc = 0 if dry_run else command_runner(["git", "add", "-A"], worktree)
                if add_rc != 0:
                    commit_rc = add_rc
                else:
                    commit_rc = 0 if dry_run else command_runner(
                        ["git", "commit", "-m", f"Automate code improvement workorders {target_date}"],
                        worktree,
                    )
    status = "dry_run_planned" if dry_run else "no_safe_orders"
    if worktree_rc != 0:
        status = worktree_status if worktree_status != "worktree_add_failed" else "worktree_failed"
    elif codex_error:
        status = _codex_error_status(codex_error)
    elif safe_orders:
        validations_pass = bool(validation_results) and all(item["exit_code"] == 0 for item in validation_results)
        acceptance_pass = validations_pass and not unsupported_acceptance_tests and all(
            item["exit_code"] == 0 for item in acceptance_results
        )
        if forbidden_scan["status"] == "fail":
            status = "blocked_forbidden_diff"
        elif validations_pass and unsupported_acceptance_tests:
            status = "unsupported_acceptance_tests"
        elif validations_pass and not acceptance_pass:
            status = "acceptance_failed"
        elif acceptance_pass and (not commit or commit_rc == 0):
            status = "committed" if commit else "validated"
        else:
            status = "validation_failed"
    if dry_run:
        status = "dry_run_planned"

    report = {
        "schema_version": 1,
        "report_type": "codex_workorder_runner",
        "date": target_date,
        "generated_at": _now(),
        "status": status,
        "dry_run": dry_run,
        "branch": branch,
        "worktree": str(worktree),
        "worktree_status": worktree_status,
        "source_generation_id": workorder.get("generation_id"),
        "implemented_orders": [
            {"order_id": item.get("order_id"), "status": "planned" if dry_run else "submitted_to_codex"}
            for item in safe_orders
        ],
        "blocked_orders": blocked_orders,
        "non_implement_triage": non_implement_triage,
        "codex_error": codex_error,
        "codex_turns": [turn.__dict__ for turn in codex_turns],
        "validation_results": validation_results,
        "acceptance_results": acceptance_results,
        "unsupported_acceptance_tests": unsupported_acceptance_tests,
        "forbidden_diff_scan": forbidden_scan,
        "commit_requested": commit,
        "commit_exit_code": commit_rc,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    json_path, md_path = _runner_paths(target_date)
    _write_json(json_path, report)
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--max-orders", type=int, default=5)
    parser.add_argument("--branch-prefix", default="codex-workorder")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    report = build_codex_workorder_runner(
        args.date,
        max_orders=args.max_orders,
        branch_prefix=args.branch_prefix,
        commit=args.commit,
        dry_run=args.dry_run,
    )
    print(json.dumps({"status": report["status"], "date": report["date"]}, ensure_ascii=False))
    return 0 if report["status"] in {"committed", "validated", "no_safe_orders", "dry_run_planned"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
