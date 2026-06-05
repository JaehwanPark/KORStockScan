"""Run safe code-improvement workorders through the Codex Python SDK."""

from __future__ import annotations

import argparse
import copy
import json
import os
import signal
import subprocess
import threading
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Sequence


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
DEFAULT_FORBIDDEN_USES = [
    "real_order_authority",
    "provider_route_change",
    "bot_restart_authority",
    "broker_guard_relaxation",
    "hard_safety_relaxation",
    "threshold_runtime_env_apply",
    "cap_release",
]

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
TERMINAL_NON_IMPLEMENT_STATUSES = {
    "no_code_required",
    "promoted_to_implement_now",
    "deferred_evidence_terminal",
    "rejected_terminal",
    "requires_user_authority",
}
COMPLETED_RUNNER_STATUSES = {"completed", "dry_run_planned"}
TWO_PASS_COMPLETED_STATUSES = {"pass2_completed", "pass2_not_required", "not_required"}


@dataclass(frozen=True)
class CodexTurnSummary:
    phase: str
    final_response: str
    model: str | None = None
    effort: str | None = None


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


def _run_codex_call_with_timeout(call: Callable[[], Any], *, phase: str) -> Any:
    raw_timeout = os.environ.get("CODEX_WORKORDER_TURN_TIMEOUT_SEC", "300")
    try:
        timeout_sec = float(raw_timeout)
    except ValueError:
        timeout_sec = 300.0
    if timeout_sec <= 0 or threading.current_thread() is not threading.main_thread():
        return call()

    def _handle_timeout(signum: int, frame: Any) -> None:
        raise TimeoutError(f"codex_turn_timeout:{phase}:{timeout_sec:g}s")

    previous = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout_sec)
    try:
        return call()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


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
    blob = _text_blob(order)
    if any(term in blob for term in FORBIDDEN_USE_TERMS):
        return "forbidden_or_not_safe"
    forbidden_uses = order.get("forbidden_uses")
    if not isinstance(forbidden_uses, list) or not any(str(item).strip() for item in forbidden_uses):
        return "missing_forbidden_uses_contract"
    return None


def _is_missing_contract_self_repairable(order: dict[str, Any]) -> bool:
    if str(order.get("decision") or "") != "implement_now":
        return False
    if order.get("runtime_effect") is not False or order.get("allowed_runtime_apply") is True:
        return False
    forbidden_uses = order.get("forbidden_uses")
    if isinstance(forbidden_uses, list) and any(str(item).strip() for item in forbidden_uses):
        return False
    blob = _text_blob(order)
    return not any(term in blob for term in FORBIDDEN_USE_TERMS)


def _self_repair_order_contract(order: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if not _is_missing_contract_self_repairable(order):
        return order, None
    repaired = dict(order)
    repaired["forbidden_uses"] = list(DEFAULT_FORBIDDEN_USES)
    recovery = {
        "order_id": order.get("order_id"),
        "status": "repaired",
        "reason": "missing_forbidden_uses_contract",
        "action": "added_default_runtime_effect_false_forbidden_uses",
        "forbidden_uses": list(DEFAULT_FORBIDDEN_USES),
    }
    return repaired, recovery


def triage_non_implement(order: dict[str, Any]) -> str:
    decision = str(order.get("decision") or "")
    status = str(order.get("implementation_status") or "")
    if status.startswith("implemented"):
        return "attached_to_existing_family"
    if decision == "attach_existing_family":
        return "needs_codex_instrumentation" if _explicitly_needs_codex_instrumentation(order) else "attached_to_existing_family"
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


def _explicitly_needs_codex_instrumentation(order: dict[str, Any]) -> bool:
    if order.get("runtime_effect") is not False or order.get("allowed_runtime_apply") is True:
        return False
    explicit_keys = (
        "needs_codex_instrumentation",
        "codex_instrumentation_required",
        "implementation_required",
    )
    if any(order.get(key) is True for key in explicit_keys):
        return True
    explicit_values = {"needs_codex_instrumentation", "instrumentation_order"}
    for key in ("implementation_status", "implementation_type", "route", "improvement_type"):
        if str(order.get(key) or "").strip().lower() in explicit_values:
            return True
    return False


def _non_implement_terminal_disposition(order: dict[str, Any]) -> str:
    decision = str(order.get("decision") or "")
    triage = triage_non_implement(order)
    if triage == "needs_codex_instrumentation" and _promotable_non_implement(order):
        return "promoted_to_implement_now"
    if decision == "reject":
        return "rejected_terminal"
    if decision == "defer_evidence":
        return "deferred_evidence_terminal"
    if triage in {"attached_to_existing_family", "stale_no_action", "drop_stale"}:
        return "no_code_required"
    return "requires_user_authority"


def _promotable_non_implement(order: dict[str, Any]) -> bool:
    if order.get("runtime_effect") is not False or order.get("allowed_runtime_apply") is True:
        return False
    blob = _text_blob(order)
    return not any(term in blob for term in FORBIDDEN_USE_TERMS)


def _promote_non_implement_order(order: dict[str, Any]) -> dict[str, Any]:
    promoted = dict(order)
    promoted["decision"] = "implement_now"
    promoted["promoted_from_decision"] = order.get("decision")
    promoted["forbidden_uses"] = promoted.get("forbidden_uses") or list(DEFAULT_FORBIDDEN_USES)
    promoted["runtime_effect"] = False
    promoted["allowed_runtime_apply"] = False
    return promoted


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Codex Workorder Runner - {report.get('date')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- implemented_order_count: `{len(report.get('implemented_orders') or [])}`",
        f"- blocked_order_count: `{len(report.get('blocked_orders') or [])}`",
        f"- dry_run: `{report.get('dry_run')}`",
        f"- worktree: `{report.get('worktree') or '-'}`",
        f"- codex_model_policy: `{report.get('codex_model_policy')}`",
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
    lines.extend(["", "## Terminal Dispositions"])
    for item in report.get("terminal_order_dispositions") or []:
        lines.append(
            f"- `{item.get('order_id')}` terminal=`{item.get('terminal_status')}` "
            f"reason=`{item.get('reason') or item.get('triage') or '-'}`"
        )
    if not report.get("terminal_order_dispositions"):
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def _order_complexity(orders: list[dict[str, Any]]) -> str:
    blob = " ".join(_text_blob(order) for order in orders)
    path_count = 0
    acceptance_count = 0
    for order in orders:
        files = order.get("files_likely_touched")
        if isinstance(files, list):
            path_count += len(files)
        tests = order.get("acceptance_tests")
        if isinstance(tests, list):
            acceptance_count += len(tests)
    broad_terms = (
        "schema",
        "producer",
        "consumer",
        "contract",
        "cross",
        "report producer",
        "traceability",
    )
    if len(orders) >= 3 or path_count >= 4 or acceptance_count >= 3 or any(term in blob for term in broad_terms):
        return "broad_contract"
    if path_count >= 2 or acceptance_count >= 1:
        return "medium_source"
    return "small_source"


def _select_turn_model_effort(
    phase: str,
    orders: list[dict[str, Any]],
    *,
    model_policy: str,
    model: str | None,
    effort: str | None,
) -> tuple[str | None, str | None]:
    if model_policy != "auto":
        return model, effort
    if model and effort:
        return model, effort
    complexity = _order_complexity(orders)
    selected: tuple[str, str]
    if phase == "implement":
        selected = ("gpt-5.4", "medium") if complexity == "broad_contract" else ("gpt-5.3-codex-spark", "medium")
    elif phase == "review":
        selected = ("gpt-5.4", "high")
    elif phase == "supplemental_fix":
        selected = ("gpt-5.4", "medium" if complexity != "broad_contract" else "high")
    elif phase == "final_review":
        selected = ("gpt-5.4", "high")
    else:
        selected = ("gpt-5.4", "medium")
    return model or selected[0], effort or selected[1]


def _make_worktree(
    target_date: str,
    branch_prefix: str,
    command_runner: CommandRunner,
    dry_run: bool,
    capture_runner: CaptureRunner | None = None,
    base_ref: str = "HEAD",
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
        root_rc, root_head = capture_runner(["git", "rev-parse", base_ref], PROJECT_ROOT)
        tree_rc, tree_head = capture_runner(["git", "rev-parse", "HEAD"], worktree)
        if root_rc != 0 or tree_rc != 0:
            return worktree, branch, 2, "worktree_head_check_failed"
        if root_head.strip() != tree_head.strip():
            return worktree, branch, 2, "worktree_stale_head"
        return worktree, branch, 0, "reused_clean_worktree"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    rc = command_runner(["git", "worktree", "add", "-B", branch, str(worktree), base_ref], PROJECT_ROOT)
    return worktree, branch, rc, "created" if rc == 0 else "worktree_add_failed"


def _preserve_and_cleanup_interrupted_worktree(
    *,
    target_date: str,
    branch: str,
    worktree: Path,
    command_runner: CommandRunner,
    dry_run: bool,
    capture_runner: CaptureRunner | None = None,
) -> dict[str, Any]:
    if dry_run:
        return {"status": "planned", "diff_path": None, "cleanup_exit_code": 0}
    if not worktree.exists():
        return {"status": "not_found", "diff_path": None, "cleanup_exit_code": 0}
    capture_runner = capture_runner or _run_capture
    diff_path = WORKTREE_ROOT / f"{branch}.interrupted.diff"
    diff_path.parent.mkdir(parents=True, exist_ok=True)

    add_intent_rc = command_runner(["git", "add", "-N", "."], worktree)
    diff_rc, diff_stdout = capture_runner(["git", "diff", "--binary", "HEAD", "--"], worktree)
    if add_intent_rc != 0 or diff_rc != 0:
        diff_path.write_text(
            f"# interrupted diff capture failed for {target_date}\n"
            f"# git_add_intent_exit_code={add_intent_rc}\n"
            f"# git_diff_exit_code={diff_rc}\n",
            encoding="utf-8",
        )
        preserve_status = "diff_capture_failed"
    else:
        diff_path.write_text(diff_stdout, encoding="utf-8")
        preserve_status = "diff_preserved" if diff_stdout.strip() else "no_diff"

    cleanup_rc = command_runner(["git", "worktree", "remove", "--force", str(worktree)], PROJECT_ROOT)
    status = preserve_status if cleanup_rc == 0 else f"{preserve_status}_cleanup_failed"
    return {"status": status, "diff_path": str(diff_path), "cleanup_exit_code": cleanup_rc}


def _codex_recovery_model_plan(model: str | None, effort: str | None) -> list[tuple[str | None, str | None, str]]:
    plan: list[tuple[str | None, str | None, str]] = [(model, effort, "requested_or_auto")]
    raw_models = os.environ.get("CODEX_WORKORDER_RECOVERY_MODELS")
    if raw_models:
        for raw_item in raw_models.split(","):
            text = raw_item.strip()
            if not text:
                continue
            if ":" in text:
                fallback_model, fallback_effort = [part.strip() or None for part in text.split(":", 1)]
            else:
                fallback_model, fallback_effort = text, os.environ.get("CODEX_WORKORDER_RECOVERY_EFFORT", "medium")
            if (fallback_model, fallback_effort) not in [(item[0], item[1]) for item in plan]:
                plan.append((fallback_model, fallback_effort, "fallback_model"))
        return plan
    fallback_model = os.environ.get("CODEX_WORKORDER_RECOVERY_MODEL", "gpt-5.3-codex-spark").strip() or None
    fallback_effort = os.environ.get("CODEX_WORKORDER_RECOVERY_EFFORT", "medium").strip() or None
    if (fallback_model, fallback_effort) != (model, effort):
        plan.append((fallback_model, fallback_effort, "fallback_model"))
    return plan


def _make_retry_worktree(
    *,
    target_date: str,
    branch_prefix: str,
    attempt_index: int,
    command_runner: CommandRunner,
    dry_run: bool,
    base_ref: str = "HEAD",
) -> tuple[Path, str, int, str]:
    retry_prefix = branch_prefix if attempt_index == 0 else f"{branch_prefix}-retry{attempt_index}"
    return _make_worktree(target_date, retry_prefix, command_runner, dry_run, base_ref=base_ref)


def _codex_turns(
    worktree: Path,
    orders: list[dict[str, Any]],
    dry_run: bool,
    *,
    model: str | None = None,
    effort: str | None = None,
    model_policy: str = "auto",
) -> tuple[list[CodexTurnSummary], str | None]:
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
        implement_model, implement_effort = _select_turn_model_effort(
            "implement", orders, model_policy=model_policy, model=model, effort=effort
        )
        thread = codex.thread_start(cwd=str(worktree), sandbox=Sandbox.workspace_write, model=implement_model)
        try:
            result = _run_codex_call_with_timeout(
                lambda: thread.run(
                    prompt,
                    **{k: v for k, v in {"model": implement_model, "effort": implement_effort}.items() if v},
                ),
                phase="implement",
            )
        except TimeoutError as exc:
            return turns, str(exc)
        turns.append(CodexTurnSummary("implement", str(getattr(result, "final_response", "")), implement_model, implement_effort))
        review_model, review_effort = _select_turn_model_effort(
            "review", orders, model_policy=model_policy, model=model, effort=effort
        )
        try:
            review = _run_codex_call_with_timeout(
                lambda: thread.run(
                    "Review the diff only. List blocking issues first.",
                    sandbox=Sandbox.read_only,
                    **{k: v for k, v in {"model": review_model, "effort": review_effort}.items() if v},
                ),
                phase="review",
            )
        except TimeoutError as exc:
            return turns, str(exc)
        turns.append(CodexTurnSummary("review", str(getattr(review, "final_response", "")), review_model, review_effort))
        fix_model, fix_effort = _select_turn_model_effort(
            "supplemental_fix", orders, model_policy=model_policy, model=model, effort=effort
        )
        try:
            fix = _run_codex_call_with_timeout(
                lambda: thread.run(
                    "Fix any blocking issues found in the review, then summarize.",
                    sandbox=Sandbox.workspace_write,
                    **{k: v for k, v in {"model": fix_model, "effort": fix_effort}.items() if v},
                ),
                phase="supplemental_fix",
            )
        except TimeoutError as exc:
            return turns, str(exc)
        turns.append(CodexTurnSummary("supplemental_fix", str(getattr(fix, "final_response", "")), fix_model, fix_effort))
        final_model, final_effort = _select_turn_model_effort(
            "final_review", orders, model_policy=model_policy, model=model, effort=effort
        )
        try:
            final_review = _run_codex_call_with_timeout(
                lambda: thread.run(
                    "Final read-only review of the resulting diff.",
                    sandbox=Sandbox.read_only,
                    **{k: v for k, v in {"model": final_model, "effort": final_effort}.items() if v},
                ),
                phase="final_review",
            )
        except TimeoutError as exc:
            return turns, str(exc)
        turns.append(CodexTurnSummary("final_review", str(getattr(final_review, "final_response", "")), final_model, final_effort))
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
            if normalized.startswith(".venv/bin/pytest "):
                normalized = "pytest " + normalized[len(".venv/bin/pytest "):]
            if normalized.startswith("./.venv/bin/pytest "):
                normalized = "pytest " + normalized[len("./.venv/bin/pytest "):]
            if normalized.startswith("venv/Scripts/python.exe "):
                normalized = "python " + normalized[len("venv/Scripts/python.exe "):]
            if not any(normalized.startswith(prefix) for prefix in ALLOWED_ACCEPTANCE_COMMAND_PREFIXES):
                unsupported.append(text)
                continue
            parts = normalized.split()
            if normalized.startswith("pytest ") or normalized.startswith("python -m pytest "):
                meaningful = [
                    part
                    for part in parts
                    if part not in {"python", "-m", "pytest"} and not part.startswith("-")
                ]
                if not any(
                    part.startswith(("src/tests/", "tests/"))
                    or part.endswith("_test.py")
                    or part.startswith("src/tests/test_")
                    for part in meaningful
                ):
                    unsupported.append(text)
                    continue
            if parts[0] == "python":
                parts[0] = _python_bin()
            elif parts[0] == "pytest":
                parts = [_python_bin(), "-m", "pytest", *parts[1:]]
            commands.append(parts)
    return commands, unsupported


def _implement_now_rejudge_reason(order: dict[str, Any]) -> str | None:
    issues = {str(item).strip() for item in (order.get("adm_issue_types") or []) if str(item).strip()}
    if issues and issues.issubset({"joined_sample_below_sample_floor", "prompt_context_not_loaded"}):
        return "evidence_waiting_sample_or_runtime_observation"
    provenance = order.get("implementation_provenance") if isinstance(order.get("implementation_provenance"), dict) else {}
    if str(provenance.get("recommended_resolution") or "") == "mark_not_applicable_explicitly":
        return "source_evidence_not_applicable_terminal"
    files = order.get("files_likely_touched")
    file_count = len([item for item in files if str(item).strip()]) if isinstance(files, list) else 0
    commands, unsupported = _acceptance_commands([order])
    source_type = str(order.get("source_report_type") or "")
    if (
        source_type in {"lifecycle_decision_matrix_holding_bucket_attribution", "lifecycle_decision_matrix_exit_bucket_attribution"}
        and file_count <= 0
        and not commands
    ):
        return "not_code_actionable_missing_files_and_acceptance"
    if (
        unsupported
        and not commands
        and order.get("order_id") == "order_swing_lifecycle_observation_coverage"
    ):
        return "not_code_actionable_unsupported_acceptance_only"
    return None


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


def _normalize_workorders(
    orders: list[dict[str, Any]],
    *,
    execute_implement_now: bool = True,
    promote_non_implement: bool = True,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    canonical: list[dict[str, Any]] = []
    normalized_out: list[dict[str, Any]] = []
    non_implement_dispositions: list[dict[str, Any]] = []
    contract_recoveries: list[dict[str, Any]] = []
    for item in orders:
        if str(item.get("decision") or "") == "implement_now":
            if not execute_implement_now:
                reason = _safe_implement_now_block_reason(item)
                non_implement_dispositions.append(
                    {
                        "order_id": item.get("order_id"),
                        "decision": item.get("decision"),
                        "terminal_status": "requires_user_authority"
                        if reason == "forbidden_or_not_safe"
                        else "deferred_evidence_terminal",
                        "triage": "non_selected_not_in_canonical_queue",
                        "reason": reason or "non_selected_not_in_canonical_queue",
                        "runtime_effect": item.get("runtime_effect"),
                        "allowed_runtime_apply": False,
                    }
                )
                continue
            recovered, recovery = _self_repair_order_contract(item)
            if recovery:
                contract_recoveries.append(recovery)
            reason = _safe_implement_now_block_reason(recovered)
            if reason is None:
                rejudge_reason = _implement_now_rejudge_reason(recovered)
                if rejudge_reason is not None:
                    normalized_out.append(
                        {
                            "order_id": item.get("order_id"),
                            "decision": "implement_now",
                            "terminal_status": "deferred_evidence_terminal",
                            "reason": rejudge_reason,
                            "runtime_effect": item.get("runtime_effect"),
                            "allowed_runtime_apply": item.get("allowed_runtime_apply"),
                        }
                    )
                    non_implement_dispositions.append(
                        {
                            "order_id": item.get("order_id"),
                            "decision": item.get("decision"),
                            "terminal_status": "deferred_evidence_terminal",
                            "triage": "rejudged_implement_now_not_code_actionable",
                            "reason": rejudge_reason,
                            "runtime_effect": item.get("runtime_effect"),
                            "allowed_runtime_apply": False,
                        }
                    )
                else:
                    canonical.append(recovered)
            else:
                normalized_out.append(
                    {
                        "order_id": item.get("order_id"),
                        "decision": "implement_now",
                        "terminal_status": "requires_user_authority" if reason == "forbidden_or_not_safe" else "rejected_terminal",
                        "reason": reason,
                        "runtime_effect": item.get("runtime_effect"),
                        "allowed_runtime_apply": item.get("allowed_runtime_apply"),
                    }
                )
            continue
        disposition = _non_implement_terminal_disposition(item)
        if disposition == "promoted_to_implement_now" and not promote_non_implement:
            disposition = "deferred_evidence_terminal"
        if disposition == "promoted_to_implement_now":
            promoted, recovery = _self_repair_order_contract(_promote_non_implement_order(item))
            if recovery:
                contract_recoveries.append(recovery)
            reason = _safe_implement_now_block_reason(promoted)
            if reason is None:
                canonical.append(promoted)
            else:
                disposition = "requires_user_authority"
                normalized_out.append(
                    {
                        "order_id": item.get("order_id"),
                        "decision": item.get("decision"),
                        "terminal_status": disposition,
                        "reason": reason,
                        "runtime_effect": item.get("runtime_effect"),
                        "allowed_runtime_apply": item.get("allowed_runtime_apply"),
                    }
                )
        non_implement_dispositions.append(
            {
                "order_id": item.get("order_id"),
                "decision": item.get("decision"),
                "terminal_status": disposition,
                "triage": triage_non_implement(item),
                "runtime_effect": item.get("runtime_effect"),
                "allowed_runtime_apply": False,
            }
        )
    return canonical, normalized_out, non_implement_dispositions, contract_recoveries


def _chunked(items: Sequence[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    chunk_size = max(1, int(size))
    return [list(items[index : index + chunk_size]) for index in range(0, len(items), chunk_size)]


def _head_sha(worktree: Path, capture_runner: CaptureRunner | None = None) -> str | None:
    capture_runner = capture_runner or _run_capture
    rc, stdout = capture_runner(["git", "rev-parse", "HEAD"], worktree)
    return stdout.strip() if rc == 0 and stdout.strip() else None


def _has_head_diff(worktree: Path, capture_runner: CaptureRunner | None = None) -> bool:
    capture_runner = capture_runner or _run_capture
    rc, stdout = capture_runner(["git", "status", "--porcelain"], worktree)
    return rc == 0 and bool(stdout.strip())


def _commit_worktree_diff(
    *,
    worktree: Path,
    target_date: str,
    command_runner: CommandRunner,
    dry_run: bool,
) -> tuple[int | None, str | None]:
    if dry_run:
        return 0, "dry_run_commit_sha"
    if not _has_head_diff(worktree):
        return 2, None
    add_rc = command_runner(["git", "add", "-A"], worktree)
    if add_rc != 0:
        return add_rc, None
    commit_rc = command_runner(["git", "commit", "-m", f"Automate code improvement workorders {target_date}"], worktree)
    if commit_rc != 0:
        return commit_rc, None
    return commit_rc, _head_sha(worktree)


def _run_branch_validation_acceptance(
    *,
    worktree: Path,
    orders: list[dict[str, Any]],
    command_runner: CommandRunner,
    dry_run: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], dict[str, Any], bool]:
    validation_results = _run_validation(worktree, command_runner, dry_run)
    validations_pass = bool(validation_results) and all(item["exit_code"] == 0 for item in validation_results)
    acceptance_results: list[dict[str, Any]] = []
    unsupported_acceptance_tests: list[str] = []
    forbidden_scan = {"status": "not_run", "matches": []}
    if validations_pass:
        acceptance_results, unsupported_acceptance_tests = _run_acceptance_tests(
            worktree,
            orders,
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
    return (
        validation_results,
        acceptance_results,
        unsupported_acceptance_tests,
        forbidden_scan,
        acceptance_pass and forbidden_scan.get("status") != "fail",
    )


def _attempt_codex_batch(
    *,
    target_date: str,
    branch_prefix: str,
    attempt_index: int,
    orders: list[dict[str, Any]],
    model: str | None,
    effort: str | None,
    model_policy: str,
    command_runner: CommandRunner,
    dry_run: bool,
    base_ref: str = "HEAD",
) -> dict[str, Any]:
    worktree, branch, worktree_rc, worktree_status = _make_retry_worktree(
        target_date=target_date,
        branch_prefix=branch_prefix,
        attempt_index=attempt_index,
        command_runner=command_runner,
        dry_run=dry_run,
        base_ref=base_ref,
    )
    result: dict[str, Any] = {
        "attempt": attempt_index + 1,
        "branch": branch,
        "worktree": str(worktree),
        "worktree_status": worktree_status,
        "base_ref": base_ref,
        "order_ids": [item.get("order_id") for item in orders],
        "model": model,
        "effort": effort,
        "codex_error": None,
        "status": "started",
        "validation_results": [],
        "acceptance_results": [],
        "unsupported_acceptance_tests": [],
        "forbidden_diff_scan": {"status": "not_run", "matches": []},
        "interrupted_worktree": {"status": "not_applicable", "diff_path": None, "cleanup_exit_code": None},
        "commit_sha": None,
    }
    if worktree_rc != 0:
        result["status"] = "worktree_failed"
        result["codex_error"] = worktree_status
        return result
    codex_turns, codex_error = _codex_turns(
        worktree,
        orders,
        dry_run,
        model=model,
        effort=effort,
        model_policy=model_policy,
    )
    result["codex_turns"] = [turn.__dict__ for turn in codex_turns]
    result["codex_error"] = codex_error
    if codex_error:
        result["status"] = "codex_error"
        if codex_error.startswith("codex_turn_timeout"):
            result["interrupted_worktree"] = _preserve_and_cleanup_interrupted_worktree(
                target_date=target_date,
                branch=branch,
                worktree=worktree,
                command_runner=command_runner,
                dry_run=dry_run,
            )
        return result
    validation_results, acceptance_results, unsupported, forbidden_scan, checks_pass = _run_branch_validation_acceptance(
        worktree=worktree,
        orders=orders,
        command_runner=command_runner,
        dry_run=dry_run,
    )
    result["validation_results"] = validation_results
    result["acceptance_results"] = acceptance_results
    result["unsupported_acceptance_tests"] = unsupported
    result["forbidden_diff_scan"] = forbidden_scan
    if not checks_pass:
        result["status"] = "validation_failed"
        return result
    commit_rc, commit_sha = _commit_worktree_diff(
        worktree=worktree,
        target_date=target_date,
        command_runner=command_runner,
        dry_run=dry_run,
    )
    result["commit_exit_code"] = commit_rc
    result["commit_sha"] = commit_sha
    result["status"] = "committed_branch" if commit_rc == 0 and commit_sha else "commit_failed"
    return result


def _expanded_timeout_values() -> list[str | None]:
    raw = os.environ.get("CODEX_WORKORDER_TURN_TIMEOUT_SEC", "300")
    values = [raw]
    try:
        doubled = str(int(float(raw) * 2))
    except ValueError:
        doubled = "600"
    if doubled not in values:
        values.append(doubled)
    return values


def _process_order_batch(
    *,
    target_date: str,
    branch_prefix: str,
    orders: list[dict[str, Any]],
    model: str | None,
    effort: str | None,
    model_policy: str,
    command_runner: CommandRunner,
    dry_run: bool,
    attempt_counter: list[int],
    recovery_attempts: list[dict[str, Any]],
    branch_commits: list[dict[str, Any]],
    max_recovery_attempts: int,
    base_ref: str = "HEAD",
) -> list[dict[str, Any]]:
    if not orders:
        return []
    order_ids = [item.get("order_id") for item in orders]
    model_plan = _codex_recovery_model_plan(model, effort)
    timeout_values = _expanded_timeout_values()
    last_result: dict[str, Any] | None = None
    original_timeout = os.environ.get("CODEX_WORKORDER_TURN_TIMEOUT_SEC")
    for timeout_value in timeout_values:
        if timeout_value is None:
            os.environ.pop("CODEX_WORKORDER_TURN_TIMEOUT_SEC", None)
        else:
            os.environ["CODEX_WORKORDER_TURN_TIMEOUT_SEC"] = timeout_value
        for attempt_model, attempt_effort, recovery_mode in model_plan:
            if attempt_counter[0] >= max_recovery_attempts:
                break
            attempt_index = attempt_counter[0]
            attempt_counter[0] += 1
            result = _attempt_codex_batch(
                target_date=target_date,
                branch_prefix=branch_prefix,
                attempt_index=attempt_index,
                orders=orders,
                model=attempt_model,
                effort=attempt_effort,
                model_policy=model_policy,
                command_runner=command_runner,
                dry_run=dry_run,
                base_ref=base_ref,
            )
            result["recovery_mode"] = recovery_mode
            result["timeout_sec"] = timeout_value
            recovery_attempts.append(result)
            last_result = result
            if result.get("status") == "committed_branch":
                branch_commits.append(
                    {
                        "branch": result.get("branch"),
                        "commit_sha": result.get("commit_sha"),
                        "order_ids": order_ids,
                    }
                )
                if original_timeout is None:
                    os.environ.pop("CODEX_WORKORDER_TURN_TIMEOUT_SEC", None)
                else:
                    os.environ["CODEX_WORKORDER_TURN_TIMEOUT_SEC"] = original_timeout
                return [
                    {
                        "order_id": item.get("order_id"),
                        "final_status": "committed_branch",
                        "attempt_count": sum(1 for attempt in recovery_attempts if item.get("order_id") in (attempt.get("order_ids") or [])),
                        "codex_errors": [
                            attempt.get("codex_error")
                            for attempt in recovery_attempts
                            if item.get("order_id") in (attempt.get("order_ids") or []) and attempt.get("codex_error")
                        ],
                        "validation_results": result.get("validation_results") or [],
                        "commit_sha": result.get("commit_sha"),
                        "branch": result.get("branch"),
                        "merged_main_sha": None,
                        "pushed": False,
                    }
                    for item in orders
                ]
        if attempt_counter[0] >= max_recovery_attempts:
            break
    if original_timeout is None:
        os.environ.pop("CODEX_WORKORDER_TURN_TIMEOUT_SEC", None)
    else:
        os.environ["CODEX_WORKORDER_TURN_TIMEOUT_SEC"] = original_timeout
    if len(orders) > 1 and attempt_counter[0] < max_recovery_attempts:
        midpoint = max(1, len(orders) // 2)
        return [
            *_process_order_batch(
                target_date=target_date,
                branch_prefix=branch_prefix,
                orders=orders[:midpoint],
                model=model,
                effort=effort,
                model_policy=model_policy,
                command_runner=command_runner,
                dry_run=dry_run,
                attempt_counter=attempt_counter,
                recovery_attempts=recovery_attempts,
                branch_commits=branch_commits,
                max_recovery_attempts=max_recovery_attempts,
                base_ref=base_ref,
            ),
            *_process_order_batch(
                target_date=target_date,
                branch_prefix=branch_prefix,
                orders=orders[midpoint:],
                model=model,
                effort=effort,
                model_policy=model_policy,
                command_runner=command_runner,
                dry_run=dry_run,
                attempt_counter=attempt_counter,
                recovery_attempts=recovery_attempts,
                branch_commits=branch_commits,
                max_recovery_attempts=max_recovery_attempts,
                base_ref=base_ref,
            ),
        ]
    return [
        {
            "order_id": item.get("order_id"),
            "final_status": "blocked_uncompleted_implementation",
            "attempt_count": sum(1 for attempt in recovery_attempts if item.get("order_id") in (attempt.get("order_ids") or [])),
            "codex_errors": [
                attempt.get("codex_error")
                for attempt in recovery_attempts
                if item.get("order_id") in (attempt.get("order_ids") or []) and attempt.get("codex_error")
            ],
            "validation_results": (last_result or {}).get("validation_results") or [],
            "commit_sha": None,
            "branch": (last_result or {}).get("branch"),
            "merged_main_sha": None,
            "pushed": False,
            "reason": (last_result or {}).get("codex_error") or (last_result or {}).get("status") or "recovery_attempts_exhausted",
        }
        for item in orders
    ]


def _merge_and_push_main(
    *,
    target_date: str,
    branch_commits: list[dict[str, Any]],
    command_runner: CommandRunner,
    dry_run: bool,
    auto_push: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not branch_commits:
        return {"status": "not_required", "merged_main_sha": None, "branches": []}, {"status": "not_required", "pushed": False}
    integration_branch = f"codex-integration-{target_date}"
    integration_worktree = WORKTREE_ROOT / integration_branch
    merge_result: dict[str, Any] = {
        "status": "started",
        "worktree": str(integration_worktree),
        "branch": integration_branch,
        "branches": [item.get("branch") for item in branch_commits],
        "merge_exit_codes": [],
        "validation_results": [],
        "merged_main_sha": None,
    }
    push_result: dict[str, Any] = {"status": "not_run", "pushed": False, "exit_code": None}
    if dry_run:
        merge_result.update({"status": "dry_run_planned", "merged_main_sha": "dry_run_main_sha"})
        push_result.update({"status": "dry_run_planned", "pushed": True, "exit_code": 0})
        return merge_result, push_result
    command_runner(["git", "fetch", "origin", "main"], PROJECT_ROOT)
    if integration_worktree.exists():
        command_runner(["git", "worktree", "remove", "--force", str(integration_worktree)], PROJECT_ROOT)
    add_rc = command_runner(["git", "worktree", "add", "-B", integration_branch, str(integration_worktree), "origin/main"], PROJECT_ROOT)
    if add_rc != 0:
        merge_result["status"] = "integration_worktree_failed"
        merge_result["worktree_add_exit_code"] = add_rc
        return merge_result, push_result
    for item in branch_commits:
        branch = str(item.get("branch") or "")
        merge_rc = command_runner(["git", "merge", "--no-ff", branch, "-m", f"Merge Codex workorder branch {branch}"], integration_worktree)
        merge_result["merge_exit_codes"].append({"branch": branch, "exit_code": merge_rc})
        if merge_rc != 0:
            merge_result["status"] = "merge_conflict"
            return merge_result, push_result
    validation_results = _run_validation(integration_worktree, command_runner, dry_run=False)
    merge_result["validation_results"] = validation_results
    if not validation_results or any(item.get("exit_code") != 0 for item in validation_results):
        merge_result["status"] = "integration_validation_failed"
        return merge_result, push_result
    merge_result["merged_main_sha"] = _head_sha(integration_worktree)
    merge_result["status"] = "merged_main"
    if not auto_push:
        push_result["status"] = "push_disabled"
        return merge_result, push_result
    push_rc = command_runner(["git", "push", "origin", "HEAD:main"], integration_worktree)
    push_result.update({"exit_code": push_rc, "status": "pushed" if push_rc == 0 else "push_rejected", "pushed": push_rc == 0})
    if push_rc != 0:
        command_runner(["git", "fetch", "origin", "main"], integration_worktree)
        rebase_rc = command_runner(["git", "rebase", "origin/main"], integration_worktree)
        push_result["rebase_exit_code"] = rebase_rc
        if rebase_rc == 0:
            validation_results = _run_validation(integration_worktree, command_runner, dry_run=False)
            push_result["post_rebase_validation_results"] = validation_results
            if validation_results and all(item.get("exit_code") == 0 for item in validation_results):
                merge_result["merged_main_sha"] = _head_sha(integration_worktree)
                push_rc = command_runner(["git", "push", "origin", "HEAD:main"], integration_worktree)
                push_result.update({"exit_code": push_rc, "status": "pushed" if push_rc == 0 else "push_rejected_after_rebase", "pushed": push_rc == 0})
    return merge_result, push_result


def _workorder_path_for_root(root: Path, target_date: str) -> Path:
    return root / "data" / "report" / "code_improvement_workorder" / f"code_improvement_workorder_{target_date}.json"


def _regeneration_commands(target_date: str, max_orders: int) -> list[list[str]]:
    return [
        [_python_bin(), "-m", "src.engine.observation_source_quality_audit", "--target-date", target_date, "--write"],
        [_python_bin(), "-m", "src.engine.automation.key_lineage_ledger", "--date", target_date],
        [_python_bin(), "-m", "src.engine.automation.conversion_lane", "--date", target_date],
        [_python_bin(), "-m", "src.engine.build_code_improvement_workorder", "--date", target_date, "--max-orders", str(max_orders)],
        [_python_bin(), "-m", "src.engine.verify_threshold_cycle_postclose_chain", "--date", target_date],
    ]


def _prepare_regeneration_worktree(
    *,
    target_date: str,
    branch_commits: list[dict[str, Any]],
    command_runner: CommandRunner,
    dry_run: bool,
) -> tuple[Path, dict[str, Any]]:
    regen_branch = f"codex-regeneration-{target_date}"
    regen_worktree = WORKTREE_ROOT / regen_branch
    result: dict[str, Any] = {
        "status": "started",
        "worktree": str(regen_worktree),
        "branch": regen_branch,
        "branches": [item.get("branch") for item in branch_commits],
        "merge_exit_codes": [],
    }
    if dry_run:
        result["status"] = "dry_run_planned"
        return regen_worktree, result
    command_runner(["git", "fetch", "origin", "main"], PROJECT_ROOT)
    if regen_worktree.exists():
        command_runner(["git", "worktree", "remove", "--force", str(regen_worktree)], PROJECT_ROOT)
    add_rc = command_runner(["git", "worktree", "add", "-B", regen_branch, str(regen_worktree), "origin/main"], PROJECT_ROOT)
    result["worktree_add_exit_code"] = add_rc
    if add_rc != 0:
        result["status"] = "regeneration_worktree_failed"
        return regen_worktree, result
    for item in branch_commits:
        branch = str(item.get("branch") or "")
        merge_rc = command_runner(["git", "merge", "--no-ff", branch, "-m", f"Merge Codex pass1 branch {branch}"], regen_worktree)
        result["merge_exit_codes"].append({"branch": branch, "exit_code": merge_rc})
        if merge_rc != 0:
            result["status"] = "regeneration_merge_conflict"
            return regen_worktree, result
    result["status"] = "merged_pass1"
    return regen_worktree, result


def _run_two_pass_regeneration(
    *,
    target_date: str,
    max_orders: int,
    branch_commits: list[dict[str, Any]],
    command_runner: CommandRunner,
    dry_run: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    regen_worktree, prep = _prepare_regeneration_worktree(
        target_date=target_date,
        branch_commits=branch_commits,
        command_runner=command_runner,
        dry_run=dry_run,
    )
    results = [prep]
    if prep.get("status") not in {"merged_pass1", "dry_run_planned"}:
        return {"status": "blocked_regeneration_failed", "worktree": str(regen_worktree), "results": results}, {}
    for command in _regeneration_commands(target_date, max_orders):
        rc = 0 if dry_run else command_runner(command, regen_worktree)
        results.append(
            {
                "status": "planned" if dry_run else ("pass" if rc == 0 else "fail"),
                "command": command,
                "exit_code": rc,
            }
        )
        if rc != 0 and not dry_run:
            return {"status": "blocked_regeneration_failed", "worktree": str(regen_worktree), "results": results}, {}
    regenerated = _load_json(_workorder_path_for_root(regen_worktree, target_date)) if not dry_run else {}
    if dry_run:
        regenerated = {}
    elif not regenerated.get("generation_id"):
        results.append(
            {
                "status": "fail",
                "command": ["load_regenerated_code_improvement_workorder", str(_workorder_path_for_root(regen_worktree, target_date))],
                "exit_code": 1,
                "reason": "regenerated_workorder_missing_or_invalid",
            }
        )
        return {"status": "blocked_regeneration_failed", "worktree": str(regen_worktree), "results": results}, {}
    return {
        "status": "regeneration_completed",
        "worktree": str(regen_worktree),
        "base_ref": prep.get("branch"),
        "results": results,
    }, regenerated


def _workorder_lineage_diff(original: dict[str, Any], regenerated: dict[str, Any]) -> dict[str, Any]:
    lineage = regenerated.get("lineage") if isinstance(regenerated.get("lineage"), dict) else {}
    original_order_ids = {str(item.get("order_id") or "") for item in original.get("orders") or [] if isinstance(item, dict)}
    regenerated_order_ids = {str(item.get("order_id") or "") for item in regenerated.get("orders") or [] if isinstance(item, dict)}
    inferred_new = sorted(item for item in regenerated_order_ids - original_order_ids if item)
    inferred_removed = sorted(item for item in original_order_ids - regenerated_order_ids if item)
    return {
        "previous_generation_id": original.get("generation_id"),
        "regenerated_generation_id": regenerated.get("generation_id"),
        "previous_source_hash": original.get("source_hash"),
        "regenerated_source_hash": regenerated.get("source_hash"),
        "new_order_ids": sorted(set(lineage.get("new_order_ids") or inferred_new)),
        "removed_order_ids": sorted(set(lineage.get("removed_order_ids") or inferred_removed)),
        "decision_changed_order_ids": sorted(set(lineage.get("decision_changed_order_ids") or [])),
        "source_hash_changed": bool(original.get("source_hash") and regenerated.get("source_hash") and original.get("source_hash") != regenerated.get("source_hash")),
    }


def _pass2_orders_from_regenerated(
    regenerated: dict[str, Any],
    *,
    completed_pass1_ids: set[str],
    lineage_diff: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]:
    changed_ids = {
        *[str(item) for item in lineage_diff.get("new_order_ids") or []],
        *[str(item) for item in lineage_diff.get("decision_changed_order_ids") or []],
    }
    selected = [item for item in regenerated.get("orders") or [] if isinstance(item, dict)]
    canonical, normalized_out, non_implement_dispositions, _recoveries = _normalize_workorders(
        selected,
        execute_implement_now=True,
        promote_non_implement=True,
    )
    pass2: list[dict[str, Any]] = []
    reasons: list[dict[str, str]] = []
    for order in canonical:
        order_id = str(order.get("order_id") or "")
        if order_id and (order_id not in completed_pass1_ids or order_id in changed_ids):
            pass2.append(order)
            reasons.append(
                {
                    "order_id": order_id,
                    "reason": "new_or_changed_order" if order_id in changed_ids else "not_completed_in_pass1",
                }
            )
    return pass2, normalized_out, non_implement_dispositions, reasons


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
    if codex_error.startswith("codex_turn_timeout"):
        return "codex_turn_timeout"
    return "codex_unavailable"


def build_codex_workorder_runner(
    target_date: str,
    *,
    max_orders: int = 5,
    branch_prefix: str = "codex-workorder",
    model: str | None = None,
    effort: str | None = None,
    model_policy: str = "auto",
    commit: bool = True,
    auto_push: bool = True,
    dry_run: bool = False,
    command_runner: CommandRunner | None = None,
) -> dict[str, Any]:
    command_runner = command_runner or _run_command
    workorder = _load_json(_workorder_path(target_date))
    original_workorder = copy.deepcopy(workorder)
    orders = [item for item in workorder.get("orders") or [] if isinstance(item, dict)]
    non_selected_orders = [item for item in workorder.get("non_selected_orders") or [] if isinstance(item, dict)]
    canonical_orders, normalized_out, non_implement_dispositions, contract_recoveries = _normalize_workorders(
        orders,
        execute_implement_now=True,
        promote_non_implement=True,
    )
    (
        _non_selected_canonical,
        _non_selected_normalized_out,
        non_selected_dispositions,
        _non_selected_contract_recoveries,
    ) = _normalize_workorders(
        non_selected_orders,
        execute_implement_now=False,
        promote_non_implement=False,
    )
    non_implement_dispositions = [*non_implement_dispositions, *non_selected_dispositions]
    batch_size = max(1, int(max_orders))
    max_recovery_attempts = max(
        1,
        int(os.environ.get("CODEX_WORKORDER_MAX_RECOVERY_ATTEMPTS", str(max(8, len(canonical_orders) * 4 or 1)))),
    )
    two_pass_enabled = _env_bool("CODEX_WORKORDER_TWO_PASS_ENABLED", True)
    recovery_attempts: list[dict[str, Any]] = []
    branch_commits: list[dict[str, Any]] = []
    attempt_counter = [0]
    order_execution_results: list[dict[str, Any]] = []
    regeneration_results: list[dict[str, Any]] = []
    workorder_lineage_diff: dict[str, Any] = {}
    pass2_selection_reason: list[dict[str, str]] = []
    pass1_order_ids = [item.get("order_id") for item in canonical_orders]
    pass2_order_ids: list[Any] = []
    two_pass_status = "not_required"
    if dry_run:
        order_execution_results = [
            {
                "order_id": item.get("order_id"),
                "final_status": "dry_run_planned",
                "attempt_count": 0,
                "codex_errors": [],
                "validation_results": [],
                "commit_sha": None,
                "merged_main_sha": None,
                "pushed": False,
            }
            for item in canonical_orders
        ]
    elif canonical_orders and not commit:
        order_execution_results = [
            {
                "order_id": item.get("order_id"),
                "final_status": "blocked_uncompleted_implementation",
                "attempt_count": 0,
                "codex_errors": [],
                "validation_results": [],
                "commit_sha": None,
                "branch": None,
                "merged_main_sha": None,
                "pushed": False,
                "reason": "commit_disabled_but_strict_completion_requires_branch_commit_main_merge_push",
            }
            for item in canonical_orders
        ]
    else:
        for batch in _chunked(canonical_orders, batch_size):
            order_execution_results.extend(
                _process_order_batch(
                    target_date=target_date,
                    branch_prefix=branch_prefix,
                    orders=batch,
                    model=model,
                    effort=effort,
                    model_policy=model_policy,
                    command_runner=command_runner,
                    dry_run=dry_run,
                    attempt_counter=attempt_counter,
                    recovery_attempts=recovery_attempts,
                    branch_commits=branch_commits,
                    max_recovery_attempts=max_recovery_attempts,
                )
            )

    pass1_complete = (
        bool(canonical_orders)
        and len(order_execution_results) == len(canonical_orders)
        and all(item.get("final_status") == "committed_branch" for item in order_execution_results)
    )
    all_canonical_orders = list(canonical_orders)
    if two_pass_enabled and not dry_run and pass1_complete:
        two_pass_status = "pass1_completed"
        regen_status, regenerated_workorder = _run_two_pass_regeneration(
            target_date=target_date,
            max_orders=max_orders,
            branch_commits=branch_commits,
            command_runner=command_runner,
            dry_run=dry_run,
        )
        regeneration_results = regen_status.get("results") or []
        if regen_status.get("status") != "regeneration_completed":
            two_pass_status = "blocked_regeneration_failed"
        else:
            two_pass_status = "regeneration_completed"
            workorder_lineage_diff = _workorder_lineage_diff(original_workorder, regenerated_workorder)
            completed_pass1_ids = {
                str(item.get("order_id") or "")
                for item in order_execution_results
                if item.get("final_status") == "committed_branch"
            }
            pass2_orders, pass2_normalized_out, pass2_non_implement, pass2_selection_reason = _pass2_orders_from_regenerated(
                regenerated_workorder,
                completed_pass1_ids=completed_pass1_ids,
                lineage_diff=workorder_lineage_diff,
            )
            normalized_out = [*normalized_out, *pass2_normalized_out]
            non_implement_dispositions = [*non_implement_dispositions, *pass2_non_implement]
            pass2_order_ids = [item.get("order_id") for item in pass2_orders]
            if pass2_orders:
                all_canonical_orders = [*all_canonical_orders, *pass2_orders]
                pass2_base_ref = str(regen_status.get("base_ref") or f"codex-regeneration-{target_date}")
                for batch in _chunked(pass2_orders, batch_size):
                    order_execution_results.extend(
                        _process_order_batch(
                            target_date=target_date,
                            branch_prefix=f"{branch_prefix}-pass2",
                            orders=batch,
                            model=model,
                            effort=effort,
                            model_policy=model_policy,
                            command_runner=command_runner,
                            dry_run=dry_run,
                            attempt_counter=attempt_counter,
                            recovery_attempts=recovery_attempts,
                            branch_commits=branch_commits,
                            max_recovery_attempts=max_recovery_attempts,
                            base_ref=pass2_base_ref,
                        )
                    )
                pass2_completed = all(
                    item.get("final_status") == "committed_branch"
                    for item in order_execution_results
                    if item.get("order_id") in set(pass2_order_ids)
                )
                two_pass_status = "pass2_completed" if pass2_completed else "blocked_new_orders_uncompleted"
            else:
                two_pass_status = "pass2_not_required"
    elif two_pass_enabled and dry_run and canonical_orders:
        two_pass_status = "pass2_not_required"
    elif two_pass_enabled and canonical_orders and not pass1_complete:
        two_pass_status = "blocked_new_orders_uncompleted"

    has_user_authority_blocker = any(
        str(item.get("terminal_status")) == "requires_user_authority" for item in normalized_out
    )
    implementation_complete = (
        bool(all_canonical_orders)
        and len(order_execution_results) == len(all_canonical_orders)
        and all(item.get("final_status") == "committed_branch" for item in order_execution_results)
        and (not two_pass_enabled or two_pass_status in TWO_PASS_COMPLETED_STATUSES)
        and not has_user_authority_blocker
    )
    merge_result = {"status": "not_required", "merged_main_sha": None, "branches": []}
    push_result = {"status": "not_required", "pushed": False}
    if implementation_complete:
        merge_result, push_result = _merge_and_push_main(
            target_date=target_date,
            branch_commits=branch_commits,
            command_runner=command_runner,
            dry_run=dry_run,
            auto_push=auto_push,
        )
        pushed = bool(push_result.get("pushed"))
        merged_sha = merge_result.get("merged_main_sha")
        if pushed:
            for item in order_execution_results:
                item["final_status"] = "completed"
                item["merged_main_sha"] = merged_sha
                item["pushed"] = True

    non_implement_complete = all(
        str(item.get("terminal_status") or "") in TERMINAL_NON_IMPLEMENT_STATUSES
        for item in non_implement_dispositions
    )
    all_implement_completed = (
        not all_canonical_orders
        or (
            len(order_execution_results) == len(all_canonical_orders)
            and all(item.get("final_status") == "completed" for item in order_execution_results)
        )
    )
    if dry_run:
        status = "dry_run_planned"
    elif two_pass_status == "blocked_regeneration_failed":
        status = "blocked_regeneration_failed"
    elif two_pass_status == "blocked_new_orders_uncompleted":
        status = "blocked_uncompleted_implementation"
    elif not canonical_orders and non_implement_complete:
        status = "completed"
    elif all_implement_completed and non_implement_complete:
        status = "completed"
    else:
        status = "blocked_uncompleted_implementation"
    if not dry_run and has_user_authority_blocker:
        status = "blocked_non_recoverable"

    completion_summary = {
        "canonical_implement_count": len(all_canonical_orders),
        "pass1_implement_count": len(pass1_order_ids),
        "pass2_implement_count": len(pass2_order_ids),
        "completed_implement_count": sum(1 for item in order_execution_results if item.get("final_status") == "completed"),
        "blocked_implement_count": sum(1 for item in order_execution_results if item.get("final_status") != "completed"),
        "normalized_out_count": len(normalized_out),
        "non_implement_terminal_count": len(non_implement_dispositions),
        "non_implement_complete": non_implement_complete,
        "main_merge_status": merge_result.get("status"),
        "push_status": push_result.get("status"),
        "pushed": bool(push_result.get("pushed")),
    }

    report = {
        "schema_version": 2,
        "report_type": "codex_workorder_runner",
        "date": target_date,
        "generated_at": _now(),
        "status": status,
        "dry_run": dry_run,
        "two_pass_mode": two_pass_enabled,
        "two_pass_status": two_pass_status,
        "batch_size": batch_size,
        "max_recovery_attempts": max_recovery_attempts,
        "codex_model": model,
        "codex_effort": effort,
        "codex_model_policy": model_policy,
        "source_generation_id": workorder.get("generation_id"),
        "canonical_implement_order_ids": [item.get("order_id") for item in all_canonical_orders],
        "pass1_order_ids": pass1_order_ids,
        "pass2_order_ids": pass2_order_ids,
        "regeneration_results": regeneration_results,
        "workorder_lineage_diff": workorder_lineage_diff,
        "pass2_selection_reason": pass2_selection_reason,
        "normalized_out_orders": normalized_out,
        "non_selected_order_ids": [item.get("order_id") for item in non_selected_orders],
        "non_selected_dispositions": non_selected_dispositions,
        "contract_recoveries": contract_recoveries,
        "order_execution_results": order_execution_results,
        "non_implement_dispositions": non_implement_dispositions,
        "recovery_attempts": recovery_attempts,
        "branch_commits": branch_commits,
        "main_merge_result": merge_result,
        "push_result": push_result,
        "completion_summary": completion_summary,
        "implemented_orders": [
            {
                "order_id": item.get("order_id"),
                "status": next(
                    (
                        result.get("final_status")
                        for result in order_execution_results
                        if result.get("order_id") == item.get("order_id")
                    ),
                    "planned" if dry_run else "not_started",
                ),
            }
            for item in all_canonical_orders
        ],
        "blocked_orders": normalized_out,
        "non_implement_triage": non_implement_dispositions,
        "terminal_order_dispositions": [*normalized_out, *non_implement_dispositions],
        "terminal_statuses": sorted(
            {
                str(item.get("terminal_status"))
                for item in [*normalized_out, *non_implement_dispositions]
                if item.get("terminal_status")
            }
        ),
        "codex_error": next(
            (
                error
                for result in order_execution_results
                for error in (result.get("codex_errors") or [])
                if error
            ),
            None,
        ),
        "codex_attempts": recovery_attempts,
        "codex_turns": [],
        "interrupted_worktree": next(
            (
                attempt.get("interrupted_worktree")
                for attempt in recovery_attempts
                if (attempt.get("interrupted_worktree") or {}).get("status") not in {None, "not_applicable"}
            ),
            {"status": "not_applicable", "diff_path": None, "cleanup_exit_code": None},
        ),
        "validation_results": [item for result in order_execution_results for item in (result.get("validation_results") or [])],
        "acceptance_results": [],
        "unsupported_acceptance_tests": [
            item
            for attempt in recovery_attempts
            for item in (attempt.get("unsupported_acceptance_tests") or [])
        ],
        "forbidden_diff_scan": next(
            (
                attempt.get("forbidden_diff_scan")
                for attempt in reversed(recovery_attempts)
                if attempt.get("forbidden_diff_scan")
            ),
            {"status": "not_run", "matches": []},
        ),
        "commit_requested": commit,
        "auto_push_main": auto_push,
        "commit_exit_code": 0 if branch_commits else None,
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
    parser.add_argument(
        "--max-orders",
        type=int,
        default=int(os.environ.get("POSTCLOSE_DONE_CONTROLLER_CODEX_BATCH_SIZE", os.environ.get("CODEX_WORKORDER_BATCH_SIZE", "5"))),
        help="Batch size for canonical implement_now orders; kept as --max-orders for compatibility.",
    )
    parser.add_argument("--branch-prefix", default="codex-workorder")
    parser.add_argument("--model", default=os.environ.get("CODEX_WORKORDER_MODEL") or None)
    parser.add_argument("--effort", default=os.environ.get("CODEX_WORKORDER_EFFORT") or None)
    parser.add_argument("--model-policy", default=os.environ.get("CODEX_WORKORDER_MODEL_POLICY") or "auto")
    parser.add_argument("--commit", dest="commit", action="store_true", default=_env_bool("CODEX_WORKORDER_COMMIT", True))
    parser.add_argument("--no-commit", dest="commit", action="store_false")
    parser.add_argument(
        "--auto-push-main",
        dest="auto_push",
        action="store_true",
        default=_env_bool("POSTCLOSE_DONE_CONTROLLER_AUTO_PUSH_MAIN", _env_bool("CODEX_WORKORDER_AUTO_PUSH_MAIN", True)),
    )
    parser.add_argument("--no-auto-push-main", dest="auto_push", action="store_false")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    report = build_codex_workorder_runner(
        args.date,
        max_orders=args.max_orders,
        branch_prefix=args.branch_prefix,
        model=args.model,
        effort=args.effort,
        model_policy=args.model_policy,
        commit=args.commit,
        auto_push=args.auto_push,
        dry_run=args.dry_run,
    )
    print(json.dumps({"status": report["status"], "date": report["date"]}, ensure_ascii=False))
    return 0 if report["status"] in COMPLETED_RUNNER_STATUSES else 1


if __name__ == "__main__":
    raise SystemExit(main())
