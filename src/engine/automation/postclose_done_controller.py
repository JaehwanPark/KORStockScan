"""Recover postclose automation into a final DONE/pass state when safe."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PROJECT_ROOT / "data" / "report"
OUTPUT_DIR = REPORT_DIR / "postclose_done_controller"
POSTCLOSE_LOG_PATH = PROJECT_ROOT / "logs" / "threshold_cycle_postclose_cron.log"
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
    "active_sim_priority_stale_seed_alias_consumed",
    "active_sim_priority_preopen_handoff_pending",
    "active_sim_priority_runtime_observation_missing",
    "active_or_hypothesis_preopen_handoff_pending",
    "ai_watching_score_smoothing_diagnostic_followup_open",
    "quote_consistency_required_fields_excluded",
    "quote_consistency_source_missing",
    "lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target",
    "swing_active_arm_priority_preopen_handoff_pending",
    "swing_active_arm_priority_runtime_observation_missing",
    "swing_lifecycle_bucket_discovery:ai_two_pass_review_fail_closed_sim_auto_blocked",
    "swing_lifecycle_bucket_discovery:ai_two_pass_review_missing_fail_closed",
    "swing_lifecycle_bucket_discovery:ai_two_pass_review_followup_required_source_only",
    "swing_lifecycle_bucket_discovery:ai_two_pass_review_followup_sim_auto_blocked",
    "swing_lifecycle_bucket_discovery:ai_two_pass_review_partial_fail_closed",
    "swing_lifecycle_bucket_discovery:ai_two_pass_review_partial_source_only",
}
FULL_WRAPPER_RERUN_LOG_ISSUES = {
    "postclose_start_marker_missing",
}
MARKER_RECONCILIATION_LOG_ISSUES = {
    "postclose_done_marker_missing",
    "postclose_fail_marker_present",
}
EV_WORKORDER_STALE_ISSUES = {
    "threshold_cycle_ev_stale_before_code_improvement_workorder",
    "threshold_cycle_ev_stale_before_pattern_lab_currentness_audit",
    "threshold_cycle_ev_stale_before_pattern_lab_propagation_audit",
}
OPTIONAL_MISSING_ARTIFACT_LABELS = {
    "threshold_preopen_apply_next",
}
_RESOURCE_PASS_RE = re.compile(r"resource guard pass label=(?P<label>\S+)")
_RESOURCE_TIMEOUT_RE = re.compile(r"resource guard timeout label=(?P<label>\S+)")
_ARTIFACT_READY_RE = re.compile(r"artifact ready label=(?P<label>\S+)")
_TAIL_REPAIR_STAGE_ORDER = (
    "key_lineage_ledger",
    "conversion_lane",
    "code_improvement_workorder_post_conversion_lane",
    "build_next_stage2_checklist",
    "verify_threshold_cycle_postclose_chain",
)


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


def _append_log_marker(line: str) -> None:
    POSTCLOSE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with POSTCLOSE_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")


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
    conversion_kpi = verification.get("conversion_kpi")
    if isinstance(conversion_kpi, dict):
        issues.extend(str(item) for item in conversion_kpi.get("issues") or [] if str(item))
        issues.extend(str(item) for item in conversion_kpi.get("warnings") or [] if str(item))
    workorder_snapshot = verification.get("workorder_snapshot")
    if isinstance(workorder_snapshot, dict) and workorder_snapshot.get("status") == "missing_snapshot_identity":
        issues.append("workorder_snapshot_missing_snapshot_identity")
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


def _structural_blockers(verification: dict[str, Any], issues: list[str]) -> list[str]:
    blockers: list[str] = []
    source_quality = verification.get("source_quality_hard_block")
    if isinstance(source_quality, dict):
        hard_count = source_quality.get("hard_blocking_contract_gap_count")
        try:
            hard_count_int = int(hard_count or 0)
        except Exception:
            hard_count_int = 0
        if hard_count_int > 0 or source_quality.get("status") == "fail":
            blockers.append("requires_code_fix:source_quality_hard_contract_gap")
    active_handoff = verification.get("active_sim_priority_handoff")
    if isinstance(active_handoff, dict):
        active_missing = [str(item) for item in active_handoff.get("missing") or [] if str(item)]
        if "active_sim_priority_inactive_key_consumed" in active_missing:
            blockers.append("requires_policy_lineage_fix:active_sim_priority_inactive_key_consumed")
        if "active_sim_priority_unknown_key_observed" in active_missing:
            blockers.append("requires_policy_lineage_fix:active_sim_priority_unknown_key_observed")
    issue_set = set(str(item) for item in issues if str(item))
    if "source_quality_hard_block_handoff_missing" in issue_set:
        blockers.append("requires_code_fix:source_quality_hard_block_handoff_missing")
    if "active_sim_priority_handoff_missing" in issue_set:
        blockers.append("requires_policy_lineage_fix:active_sim_priority_handoff_missing")
    return list(dict.fromkeys(blockers))


def _structural_next_actions(blockers: list[str]) -> list[str]:
    actions: list[str] = []
    for blocker in blockers:
        if blocker.startswith("requires_code_fix:source_quality"):
            actions.append("fix_source_quality_metric_contract_and_rerun_postclose_audit")
        elif blocker.startswith("requires_policy_lineage_fix:active_sim_priority"):
            actions.append("fix_active_sim_priority_seed_lineage_and_verify_no_inactive_runtime_key")
    return list(dict.fromkeys(actions))


def _has_done_marker(verification: dict[str, Any]) -> bool:
    marker = str(verification.get("latest_done_marker") or "").strip()
    return bool(marker and marker != "-")


def _postclose_status_succeeded(target_date: str) -> bool:
    return str(_load_json(_status_path(target_date)).get("status") or "") == "succeeded"


def _is_done_verifier_status(target_date: str, verification: dict[str, Any], issues: list[str]) -> bool:
    verifier_status = str(verification.get("status") or "")
    if verifier_status == "pass":
        return _has_done_marker(verification) and _postclose_status_succeeded(target_date)
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


def _build_tuning_performance_control_tower_action(target_date: str) -> RecoveryAction:
    return RecoveryAction(
        "refresh_tuning_performance_control_tower",
        [
            _python_bin(),
            "-m",
            "src.engine.automation.tuning_performance_control_tower",
            "--date",
            target_date,
        ],
        "wrapper tail repair post-DONE tuning performance control tower",
    )


def _build_pending_verify_action(target_date: str) -> RecoveryAction:
    return RecoveryAction(
        "verify_postclose_chain_pending_done",
        [
            _python_bin(),
            "-m",
            "src.engine.verify_threshold_cycle_postclose_chain",
            "--date",
            target_date,
            "--allow-pending-done-marker",
        ],
        "wrapper-tail repair verifier before DONE reconciliation",
    )


def _next_calendar_date(target_date: str) -> str:
    try:
        return (date.fromisoformat(target_date) + timedelta(days=1)).isoformat()
    except ValueError:
        return target_date


def _build_next_preopen_apply_action(target_date: str) -> RecoveryAction:
    next_date = _next_calendar_date(target_date)
    return RecoveryAction(
        "refresh_next_preopen_apply",
        [
            _python_bin(),
            "-m",
            "src.engine.threshold_cycle_preopen_apply",
            "--date",
            next_date,
            "--source-date",
            target_date,
            "--source-phase",
            "postclose",
            "--apply-mode",
            "auto_bounded_live",
            "--auto-apply",
        ],
        "refresh next PREOPEN apply plan after postclose sim-auto/catalog artifacts",
    )


def _build_runtime_apply_gap_audit_action(target_date: str) -> RecoveryAction:
    return RecoveryAction(
        "refresh_runtime_apply_gap_audit",
        [_python_bin(), "-m", "src.engine.runtime_apply_gap_audit", "--date", target_date],
        "runtime apply gap audit refresh after next PREOPEN apply",
    )


def _build_marker_reconciliation_action(target_date: str) -> RecoveryAction:
    return RecoveryAction(
        "marker_reconciliation",
        None,
        "marker reconciliation without full wrapper rerun",
    )


def _build_tail_done_reconciliation_action(target_date: str) -> RecoveryAction:
    return RecoveryAction(
        "tail_repair_done_reconciliation",
        None,
        "DONE/status reconciliation after wrapper-tail minimal repair",
    )


def _env_enabled(name: str, default: str = "true") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true"}


def _build_codex_runner_action(target_date: str) -> RecoveryAction:
    return RecoveryAction(
        "run_codex_workorder_runner",
        [_python_bin(), "-m", "src.engine.automation.codex_workorder_runner", "--date", target_date],
        "codex workorder runner strict completion or 2-pass incomplete",
    )


def _verification_artifacts_passable(verification: dict[str, Any]) -> bool:
    if verification.get("missing_required_artifacts"):
        return False
    if verification.get("missing_downstream_links"):
        return False
    artifact_status = verification.get("artifact_status")
    if not isinstance(artifact_status, list) or not artifact_status:
        return False
    for item in artifact_status:
        if not isinstance(item, dict) or not item.get("label") or "exists" not in item:
            return False
        if item.get("exists") is False and item.get("label") in OPTIONAL_MISSING_ARTIFACT_LABELS:
            continue
        if item.get("json_valid") is False:
            return False
    return True


def _has_invalid_artifact_status(verification: dict[str, Any]) -> bool:
    artifact_status = verification.get("artifact_status") or []
    if not isinstance(artifact_status, list):
        return True
    for item in artifact_status:
        if not isinstance(item, dict) or not item.get("label") or "exists" not in item:
            return True
        if item.get("exists") is False and item.get("label") in OPTIONAL_MISSING_ARTIFACT_LABELS:
            continue
        if item.get("json_valid") is False:
            return True
    return False


def _latest_postclose_run_lines(target_date: str) -> list[str]:
    if not POSTCLOSE_LOG_PATH.exists():
        return []
    try:
        lines = POSTCLOSE_LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    start_prefix = f"[START] threshold-cycle postclose target_date={target_date}"
    start_index: int | None = None
    for index, line in enumerate(lines):
        if start_prefix in line:
            start_index = index
    return lines[start_index:] if start_index is not None else []


def _postclose_run_segments(target_date: str) -> list[list[str]]:
    if not POSTCLOSE_LOG_PATH.exists():
        return []
    try:
        lines = POSTCLOSE_LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    start_prefix = f"[START] threshold-cycle postclose target_date={target_date}"
    segments: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if start_prefix in line:
            if current:
                segments.append(current)
            current = [line]
        elif current:
            current.append(line)
    if current:
        segments.append(current)
    return segments


def _failed_tail_stage_from_run_lines(target_date: str, run_lines: list[str]) -> str | None:
    if not run_lines:
        return None
    if not any(f"[FAIL] threshold-cycle postclose target_date={target_date}" in line for line in run_lines):
        return None
    if any(f"[DONE] threshold-cycle postclose target_date={target_date}" in line for line in run_lines):
        return None

    for line in reversed(run_lines):
        timeout = _RESOURCE_TIMEOUT_RE.search(line)
        if timeout:
            label = timeout.group("label")
            return label if label in _TAIL_REPAIR_STAGE_ORDER else None

    ready_labels: set[str] = set()
    last_pass_label: str | None = None
    for line in run_lines:
        ready = _ARTIFACT_READY_RE.search(line)
        if ready:
            ready_labels.add(ready.group("label"))
            continue
        resource_pass = _RESOURCE_PASS_RE.search(line)
        if resource_pass:
            last_pass_label = resource_pass.group("label")

    if last_pass_label in _TAIL_REPAIR_STAGE_ORDER and last_pass_label not in ready_labels:
        return last_pass_label
    return None


def _latest_failed_tail_stage(target_date: str) -> str | None:
    for run_lines in reversed(_postclose_run_segments(target_date)):
        failed_stage = _failed_tail_stage_from_run_lines(target_date, run_lines)
        if failed_stage:
            return failed_stage
    return None


def _tail_stage_repair_actions(target_date: str, failed_stage: str) -> list[RecoveryAction]:
    workorder_max_orders = os.environ.get("CODE_IMPROVEMENT_WORKORDER_MAX_ORDERS", "12")
    stage_commands = {
        "key_lineage_ledger": RecoveryAction(
            "refresh_key_lineage_ledger",
            [_python_bin(), "-m", "src.engine.automation.key_lineage_ledger", "--date", target_date],
            "wrapper tail repair from failed key lineage ledger stage",
        ),
        "conversion_lane": RecoveryAction(
            "refresh_conversion_lane",
            [_python_bin(), "-m", "src.engine.automation.conversion_lane", "--date", target_date],
            "wrapper tail repair from failed conversion lane stage",
        ),
        "code_improvement_workorder_post_conversion_lane": RecoveryAction(
            "refresh_code_improvement_workorder",
            [
                _python_bin(),
                "-m",
                "src.engine.build_code_improvement_workorder",
                "--date",
                target_date,
                "--max-orders",
                workorder_max_orders,
            ],
            "wrapper tail repair from post-conversion workorder stage",
        ),
        "build_next_stage2_checklist": RecoveryAction(
            "refresh_next_stage2_checklist",
            [
                _python_bin(),
                "-m",
                "src.engine.build_next_stage2_checklist",
                "--source-date",
                target_date,
            ],
            "wrapper tail repair from next checklist stage",
        ),
    }
    stage_index = _TAIL_REPAIR_STAGE_ORDER.index(failed_stage)
    actions: list[RecoveryAction] = []
    for stage in _TAIL_REPAIR_STAGE_ORDER[stage_index:]:
        action = stage_commands.get(stage)
        if action is not None:
            actions.append(action)
    actions.extend(
        [
            RecoveryAction(
                "refresh_pattern_lab_currentness_audit",
                [_python_bin(), "-m", "src.engine.pattern_lab_currentness_audit", "--date", target_date],
                "wrapper tail repair pattern currentness audit refresh before final EV",
            ),
            RecoveryAction(
                "refresh_pattern_lab_propagation_audit",
                [_python_bin(), "-m", "src.engine.pattern_lab_propagation_audit", "--date", target_date],
                "wrapper tail repair pattern propagation audit refresh before final EV",
            ),
            RecoveryAction(
                "refresh_code_improvement_workorder",
                [
                    _python_bin(),
                    "-m",
                    "src.engine.build_code_improvement_workorder",
                    "--date",
                    target_date,
                    "--max-orders",
                    workorder_max_orders,
                ],
                "wrapper tail repair workorder refresh before final EV",
            ),
            RecoveryAction(
                "refresh_threshold_cycle_ev",
                [_python_bin(), "-m", "src.engine.threshold_cycle_ev_report", "--date", target_date],
                "wrapper tail repair EV refresh after upstream audits and workorder",
            ),
            RecoveryAction(
                "refresh_runtime_approval_summary",
                [_python_bin(), "-m", "src.engine.runtime_approval_summary", "--date", target_date],
                "wrapper tail repair runtime summary refresh after EV consumers",
            ),
            _build_next_preopen_apply_action(target_date),
            _build_runtime_apply_gap_audit_action(target_date),
            _build_pending_verify_action(target_date),
            _build_tail_done_reconciliation_action(target_date),
            _build_verify_action(target_date),
        ]
    )
    if _env_enabled("THRESHOLD_CYCLE_RUN_TUNING_PERFORMANCE_CONTROL_TOWER"):
        actions.append(_build_tuning_performance_control_tower_action(target_date))
    return actions


def _tail_stage_from_actions(actions_done: list[dict[str, Any]]) -> str | None:
    action_to_stage = {
        "refresh_key_lineage_ledger": "key_lineage_ledger",
        "refresh_conversion_lane": "conversion_lane",
        "refresh_code_improvement_workorder": "code_improvement_workorder_post_conversion_lane",
        "refresh_next_stage2_checklist": "build_next_stage2_checklist",
        "verify_postclose_chain_pending_done": "verify_threshold_cycle_postclose_chain",
    }
    for item in actions_done:
        stage = action_to_stage.get(str(item.get("action") or ""))
        if stage:
            return stage
    return None


def _can_finalize_tail_repair(verification: dict[str, Any]) -> bool:
    verifier_status = str(verification.get("status") or "")
    if verifier_status not in {"pass", "warning", "pass_with_pending_done_marker"}:
        return False
    flattened_issues = set(_flatten_issues(verification))
    allowed_issues = MARKER_RECONCILIATION_LOG_ISSUES | {"postclose_done_marker_missing"} | DONE_ACCEPTABLE_WARNING_ISSUES
    if flattened_issues and not flattened_issues.issubset(allowed_issues):
        return False
    if verification.get("missing_required_artifacts"):
        return False
    if verification.get("missing_downstream_links") or verification.get("stale_downstream_links"):
        return False
    if verification.get("source_generation_warnings"):
        return False
    if not _verification_artifacts_passable(verification):
        return False
    if _has_invalid_artifact_status(verification):
        return False
    return True


def _can_attempt_failed_done_reconciliation(target_date: str, verification: dict[str, Any]) -> bool:
    if _postclose_status_succeeded(target_date):
        return False
    predecessor = verification.get("predecessor_integrity")
    log_issues = (
        set(str(item) for item in predecessor.get("log_issues") or [] if str(item))
        if isinstance(predecessor, dict)
        else set()
    )
    if log_issues != {"postclose_fail_marker_present"}:
        return False
    flattened_issues = set(_flatten_issues(verification))
    allowed_issues = {"postclose_fail_marker_present"} | DONE_ACCEPTABLE_WARNING_ISSUES
    if flattened_issues and not flattened_issues.issubset(allowed_issues):
        return False
    if verification.get("missing_required_artifacts"):
        return False
    if verification.get("missing_downstream_links") or verification.get("stale_downstream_links"):
        return False
    if verification.get("source_generation_warnings"):
        return False
    if not _verification_artifacts_passable(verification):
        return False
    if _has_invalid_artifact_status(verification):
        return False
    runtime_gap = verification.get("runtime_apply_gap_audit")
    if isinstance(runtime_gap, dict) and runtime_gap.get("status") == "fail":
        return False
    conversion_kpi = verification.get("conversion_kpi")
    if isinstance(conversion_kpi, dict) and conversion_kpi.get("status") == "fail":
        return False
    workorder_snapshot = verification.get("workorder_snapshot")
    if isinstance(workorder_snapshot, dict) and workorder_snapshot.get("status") == "missing_snapshot_identity":
        return False
    return True


def _can_reconcile_marker(target_date: str, verification: dict[str, Any]) -> bool:
    if not _postclose_status_succeeded(target_date):
        return False
    predecessor = verification.get("predecessor_integrity")
    log_issues = (
        set(str(item) for item in predecessor.get("log_issues") or [] if str(item))
        if isinstance(predecessor, dict)
        else set()
    )
    if not log_issues or not log_issues.issubset(MARKER_RECONCILIATION_LOG_ISSUES):
        return False
    if predecessor and isinstance(predecessor, dict) and predecessor.get("timeouts"):
        return False
    allowed_reconciliation_issues = MARKER_RECONCILIATION_LOG_ISSUES | DONE_ACCEPTABLE_WARNING_ISSUES
    flattened_issues = set(_flatten_issues(verification))
    if flattened_issues and not flattened_issues.issubset(allowed_reconciliation_issues):
        return False
    if not _verification_artifacts_passable(verification):
        return False
    if verification.get("stale_downstream_links"):
        return False
    if verification.get("source_generation_warnings"):
        return False
    warning_issues = [
        str(item)
        for item in [
            *(verification.get("handoff_warnings") or []),
            *(((verification.get("conversion_kpi") or {}).get("warnings") or []) if isinstance(verification.get("conversion_kpi"), dict) else []),
        ]
        if str(item)
    ]
    if warning_issues and not set(warning_issues).issubset(DONE_ACCEPTABLE_WARNING_ISSUES):
        return False
    if verification.get("runtime_apply_gap_issues"):
        return False
    runtime_gap = verification.get("runtime_apply_gap_audit")
    if isinstance(runtime_gap, dict) and runtime_gap.get("status") == "fail":
        return False
    conversion_kpi = verification.get("conversion_kpi")
    if isinstance(conversion_kpi, dict) and conversion_kpi.get("status") == "fail":
        return False
    workorder_snapshot = verification.get("workorder_snapshot")
    if isinstance(workorder_snapshot, dict) and workorder_snapshot.get("status") == "missing_snapshot_identity":
        return False
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
            return False
    return True


def _run_internal_action(target_date: str, action: RecoveryAction, verification: dict[str, Any]) -> int:
    if action.action not in {"marker_reconciliation", "tail_repair_done_reconciliation"}:
        raise ValueError(f"unsupported internal action: {action.action}")
    if action.action == "marker_reconciliation":
        if not _can_reconcile_marker(target_date, verification):
            return 1
        recovery_action = "marker_reconciliation"
    else:
        if not _can_finalize_tail_repair(verification):
            return 1
        recovery_action = "tail_repair_done_reconciliation"
        status_path = _status_path(target_date)
        status_payload = _load_json(status_path)
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        status_payload.update(
            {
                "status": "succeeded",
                "reason": "tail_repair_done_reconciliation",
                "exit_code": 0,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "finished_at": now,
                "updated_at": now,
            }
        )
        _write_json(status_path, status_payload)
    finished_at = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    _append_log_marker(
        "[DONE] threshold-cycle postclose "
        f"target_date={target_date} recovery_action={recovery_action} "
        f"full_wrapper_rerun=false finished_at={finished_at}"
    )
    return 0


def _recovery_actions(target_date: str, verification: dict[str, Any], *, allow_wrapper_rerun: bool) -> list[RecoveryAction]:
    issues = _flatten_issues(verification)
    actions: list[RecoveryAction] = []
    issue_text = " ".join(issues)
    log_issues = (
        ((verification.get("predecessor_integrity") or {}).get("log_issues") or [])
        if isinstance(verification.get("predecessor_integrity"), dict)
        else []
    )
    log_issue_set = {str(item) for item in log_issues if str(item)}
    failed_tail_stage = _latest_failed_tail_stage(target_date)
    if allow_wrapper_rerun and log_issue_set & FULL_WRAPPER_RERUN_LOG_ISSUES:
        actions.append(
            RecoveryAction(
                "rerun_threshold_cycle_postclose",
                ["bash", "deploy/run_threshold_cycle_postclose.sh", target_date],
                "wrapper start marker missing",
            )
        )
        return actions
    if allow_wrapper_rerun and (verification.get("missing_required_artifacts") or _has_invalid_artifact_status(verification)):
        actions.append(
            RecoveryAction(
                "rerun_threshold_cycle_postclose",
                ["bash", "deploy/run_threshold_cycle_postclose.sh", target_date],
                "required artifact missing or invalid",
            )
        )
        return actions
    if "postclose_fail_marker_present" in log_issue_set and failed_tail_stage:
        return _tail_stage_repair_actions(target_date, failed_tail_stage)
    if log_issue_set & MARKER_RECONCILIATION_LOG_ISSUES and _can_reconcile_marker(target_date, verification):
        actions.extend([_build_marker_reconciliation_action(target_date), _build_verify_action(target_date)])
        return actions
    if "postclose_fail_marker_present" in log_issue_set and _can_attempt_failed_done_reconciliation(
        target_date, verification
    ):
        actions.extend(
            [
                _build_pending_verify_action(target_date),
                _build_tail_done_reconciliation_action(target_date),
                _build_verify_action(target_date),
            ]
        )
        return actions
    if "active_sim_priority_handoff_missing" in issues:
        actions.extend(
            [
                _build_next_preopen_apply_action(target_date),
                _build_runtime_apply_gap_audit_action(target_date),
                _build_pending_verify_action(target_date),
                _build_tail_done_reconciliation_action(target_date),
                _build_verify_action(target_date),
            ]
        )
        return actions
    if "runtime_apply_gap_audit_stale_before_threshold_preopen_apply" in issues:
        actions.extend(
            [
                _build_runtime_apply_gap_audit_action(target_date),
                _build_pending_verify_action(target_date),
                _build_tail_done_reconciliation_action(target_date),
                _build_verify_action(target_date),
            ]
        )
        return actions
    if EV_WORKORDER_STALE_ISSUES & set(issues):
        actions.extend(
            [
                RecoveryAction(
                    "refresh_daily_threshold_cycle_report",
                    [
                        _python_bin(),
                        "-m",
                        "src.engine.daily_threshold_cycle_report",
                        "--date",
                        target_date,
                        "--calibration-run-phase",
                        "postclose",
                        "--ai-correction-provider",
                        "openai",
                        "--reuse-ai-review-if-valid",
                    ],
                    "daily report refresh before EV/workorder repair",
                ),
                RecoveryAction(
                    "refresh_threshold_cycle_ev",
                    [_python_bin(), "-m", "src.engine.threshold_cycle_ev_report", "--date", target_date],
                    "threshold EV source refresh before downstream consumers",
                ),
                RecoveryAction(
                    "refresh_pattern_lab_currentness_audit",
                    [_python_bin(), "-m", "src.engine.pattern_lab_currentness_audit", "--date", target_date],
                    "pattern currentness audit refresh after EV",
                ),
                RecoveryAction(
                    "refresh_pattern_lab_propagation_audit",
                    [_python_bin(), "-m", "src.engine.pattern_lab_propagation_audit", "--date", target_date],
                    "pattern propagation audit refresh after EV",
                ),
                RecoveryAction(
                    "refresh_code_improvement_workorder",
                    [_python_bin(), "-m", "src.engine.build_code_improvement_workorder", "--date", target_date],
                    "workorder lineage repair after EV and pattern consumers",
                ),
                RecoveryAction(
                    "refresh_runtime_approval_summary",
                    [_python_bin(), "-m", "src.engine.runtime_approval_summary", "--date", target_date],
                    "runtime summary refresh after EV consumer repair",
                ),
                _build_next_preopen_apply_action(target_date),
                _build_runtime_apply_gap_audit_action(target_date),
                _build_verify_action(target_date),
            ]
        )
        return actions
    if "runtime_apply_gap" in issue_text:
        actions.append(_build_runtime_apply_gap_audit_action(target_date))
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
        f"- root_cause: `{report.get('root_cause')}`",
        f"- selected_recovery_action: `{report.get('selected_recovery_action')}`",
        f"- full_wrapper_rerun_used: `{report.get('full_wrapper_rerun_used')}`",
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
    structural = report.get("structural_blockers") or []
    if structural:
        lines.extend(["", "## Structural Blockers"])
        lines.extend(f"- `{item}`" for item in structural)
        lines.append(f"- requires_code_fix: `{report.get('requires_code_fix')}`")
        lines.append(f"- requires_policy_lineage_fix: `{report.get('requires_policy_lineage_fix')}`")
    next_actions = report.get("structural_next_actions") or []
    if next_actions:
        lines.extend(["", "## Structural Next Actions"])
        lines.extend(f"- `{item}`" for item in next_actions)
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
    observed_root_causes: list[str] = []

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
        if verifier_status not in {"pass", "warning"} or issues:
            observed_root_causes.extend(issues or [f"verifier_status={verifier_status}"])
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
            if dry_run:
                rc = 0
            elif action.command is None:
                rc = _run_internal_action(target_date, action, final_verifier)
            else:
                rc = command_runner(action.command or [], _action_env(action))
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
            if action.action.startswith("verify_postclose_chain") and rc == 0:
                final_verifier = _load_json(_verification_path(target_date))
            if rc != 0 and not dry_run:
                blocked_reasons.append(f"{action.action}_failed")
                break
        if blocked_reasons:
            break

    final_status = str(final_verifier.get("status") or "missing")
    final_issues = _flatten_issues(final_verifier)
    structural_blockers = _structural_blockers(final_verifier, final_issues)
    structural_next_actions = _structural_next_actions(structural_blockers)
    latest_failed_tail_stage = _latest_failed_tail_stage(target_date) or _tail_stage_from_actions(actions_done)
    selected_recovery_action = next(
        (
            item["action"]
            for item in actions_done
            if item.get("action") not in {"verify_postclose_chain"}
        ),
        None,
    )
    full_wrapper_rerun_used = any(item.get("action") == "rerun_threshold_cycle_postclose" for item in actions_done)
    minimal_repair_commands = [
        item.get("command")
        for item in actions_done
        if item.get("action") != "rerun_threshold_cycle_postclose" and item.get("command")
    ]
    root_cause_items = list(dict.fromkeys(observed_root_causes or final_issues or [f"verifier_status={final_status}"]))
    root_cause = ",".join(root_cause_items)
    blocked_reason = ",".join(blocked_reasons) if blocked_reasons else None
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
    elif structural_blockers:
        status = "blocked_structural_contract_gap"
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
        "root_cause": root_cause,
        "selected_recovery_action": selected_recovery_action,
        "latest_failed_tail_stage": latest_failed_tail_stage,
        "tail_stage_minimal_repair_supported": latest_failed_tail_stage is not None,
        "full_wrapper_rerun_allowed": allow_wrapper_rerun,
        "full_wrapper_rerun_used": full_wrapper_rerun_used,
        "minimal_repair_commands": minimal_repair_commands,
        "blocked_reason": blocked_reason,
        "structural_blockers": structural_blockers,
        "requires_code_fix": any(str(item).startswith("requires_code_fix:") for item in structural_blockers),
        "requires_policy_lineage_fix": any(
            str(item).startswith("requires_policy_lineage_fix:") for item in structural_blockers
        ),
        "structural_next_actions": structural_next_actions,
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
        default=os.environ.get("POSTCLOSE_DONE_CONTROLLER_REQUIRE_CODEX_COMPLETED", "false").strip().lower()
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
