"""Runtime helpers for monitor snapshot async dispatch and completion signals."""

from __future__ import annotations

import json
import copy
import inspect
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parents[2]
TMP_DIR = PROJECT_DIR / "tmp"
DEPLOY_DIR = PROJECT_DIR / "deploy"
LOG_FILE = PROJECT_DIR / "logs" / "run_monitor_snapshot.log"
HEAVY_SNAPSHOT_PROFILE_BY_KIND = {
    "performance_tuning": "intraday_light",
    "trade_review": "intraday_light",
    "post_sell_feedback": "full",
    "holding_exit_observation": "full",
}

ASYNC_RESPONSE_RE = re.compile(
    r"^\[INFO\] monitor snapshot async response "
    r"status=(?P<status>[a-z_]+) "
    r"date=(?P<target_date>\d{4}-\d{2}-\d{2}) "
    r"profile=(?P<profile>[a-z_]+) "
    r"worker_pid=(?P<worker_pid>[^ ]+) "
    r"output_file=(?P<output_file>.+)$"
)
TAIL_READ_BYTES = 256 * 1024


def completion_artifact_path(target_date: str, profile: str) -> Path:
    safe_profile = str(profile or "full").strip().lower().replace("-", "_")
    return TMP_DIR / f"monitor_snapshot_completion_{target_date}_{safe_profile}.json"


def load_json_line(path: Path | str | None) -> dict[str, Any]:
    if not path:
        return {}
    target = Path(path)
    if not target.exists():
        return {}
    try:
        size = target.stat().st_size
        with target.open("rb") as handle:
            handle.seek(max(0, size - TAIL_READ_BYTES))
            text = handle.read().decode("utf-8", errors="replace")
    except OSError:
        return {}
    payload: dict[str, Any] = {}
    for raw_line in reversed(text.splitlines()):
        line = raw_line.strip()
        if not line.startswith("{") or not line.endswith("}"):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            payload = parsed
            break
    return payload


def normalize_result_payload(
    *,
    target_date: str,
    profile: str,
    result_file: str | None = None,
    output_text: str | None = None,
    status_override: str | None = None,
    worker_pid: str | None = None,
    output_file: str | None = None,
    log_file: str | None = None,
) -> dict[str, Any]:
    payload = load_json_line(result_file)
    text = str(output_text or "")
    status = str(status_override or payload.get("status") or "").strip().lower()

    if not status:
        if "snapshot cooldown active" in text:
            status = "skipped"
            payload.setdefault("reason", "cooldown_active")
        elif "run_snapshot already running" in text:
            status = "skipped"
            payload.setdefault("reason", "lock_busy")
        elif "existing full snapshot manifest detected" in text:
            status = "skipped"
            payload.setdefault("reason", "existing_manifest")
        elif "PREOPEN full build blocked" in text:
            status = "skipped"
            payload.setdefault("reason", "preopen_blocked")
        elif payload:
            status = "success"

    if not status:
        status = "unknown"

    snapshots = payload.get("snapshots")
    if not isinstance(snapshots, dict):
        snapshots = {}

    next_prompt_hint = {
        "success": "snapshot 결과를 확인하고 다음 판정 프롬프트를 이어서 입력하세요.",
        "failed": "error/log를 확인한 뒤 원인 수정 또는 재실행 프롬프트를 입력하세요.",
        "skipped": "이미 최신 결과가 있거나 실행 중입니다. 중복 실행 대신 기존 결과를 확인하세요.",
        "dispatched": "completion artifact 갱신 후 결과 기반 다음 프롬프트를 입력하세요.",
        "already_running": "기존 백그라운드 작업의 completion artifact와 결과 파일을 확인하세요.",
        "unknown": "상태를 확인한 뒤 다음 프롬프트를 입력하세요.",
    }.get(status, "상태를 확인한 뒤 다음 프롬프트를 입력하세요.")

    finished_at = payload.get("finished_at")
    started_at = payload.get("started_at")
    now_display = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if status in {"dispatched", "already_running"}:
        finished_at = None
        started_at = started_at or now_display
    else:
        finished_at = finished_at or now_display
        started_at = started_at or finished_at

    reason = payload.get("reason")
    if status == "already_running" and not reason:
        reason = "already_running"

    normalized = {
        "status": status,
        "target_date": target_date,
        "profile": profile,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_sec": payload.get("duration_sec"),
        "reason": reason,
        "error_kind": payload.get("error_kind"),
        "error": payload.get("error"),
        "worker_pid": worker_pid or payload.get("worker_pid"),
        "result_file": result_file or payload.get("result_file"),
        "output_file": output_file or result_file or payload.get("output_file"),
        "log_file": log_file or payload.get("log_file") or str(LOG_FILE),
        "snapshot_count": len(
            [
                key
                for key in snapshots
                if key
                not in {
                    "profile",
                    "io_delay_sec",
                    "trend_max_dates",
                    "io_delay_sec_per_stage",
                    "snapshot_manifest",
                    "server_comparison_status",
                    "server_comparison_error",
                }
                and not str(key).startswith("server_comparison_")
            ]
        ),
        "snapshots": snapshots,
        "next_prompt_hint": next_prompt_hint,
    }
    return normalized


def write_completion_artifact(path: Path | str, payload: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return target


def load_completion_artifact(target_date: str, profile: str) -> dict[str, Any]:
    path = completion_artifact_path(target_date, profile)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def parse_async_dispatch_response(
    stdout: str, *, target_date: str, profile: str
) -> dict[str, Any]:
    status = "failed"
    worker_pid = ""
    output_file = ""
    for raw_line in stdout.splitlines():
        match = ASYNC_RESPONSE_RE.match(raw_line.strip())
        if not match:
            continue
        if match.group("target_date") != target_date:
            continue
        if match.group("profile") != profile:
            continue
        status = match.group("status")
        worker_pid = match.group("worker_pid").strip()
        output_file = match.group("output_file").strip()
    return {
        "status": status,
        "worker_pid": "" if worker_pid == "-" else worker_pid,
        "output_file": "" if output_file == "-" else output_file,
    }


def dispatch_monitor_snapshot_job(
    *,
    target_date: str,
    profile: str,
    notify_admin: bool = False,
) -> dict[str, Any]:
    normalized_profile = str(profile or "full").strip().lower().replace("-", "_")
    if normalized_profile not in {"full", "intraday_light"}:
        raise ValueError(f"unsupported snapshot profile: {profile}")

    script = (
        DEPLOY_DIR / "run_monitor_snapshot_midcheck_safe.sh"
        if normalized_profile == "intraday_light"
        else DEPLOY_DIR / "run_monitor_snapshot_cron.sh"
    )
    env = os.environ.copy()
    env["MONITOR_SNAPSHOT_ASYNC"] = "1"
    env["MONITOR_SNAPSHOT_NOTIFY_ONLY"] = "1"
    env["MONITOR_SNAPSHOT_NOTIFY_ADMIN"] = "1" if notify_admin else "0"

    proc = subprocess.run(
        [str(script), target_date],
        cwd=str(PROJECT_DIR),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    parsed = parse_async_dispatch_response(
        proc.stdout, target_date=target_date, profile=normalized_profile
    )
    artifact_path = completion_artifact_path(target_date, normalized_profile)
    normalized = normalize_result_payload(
        target_date=target_date,
        profile=normalized_profile,
        status_override=parsed["status"] if proc.returncode == 0 else "failed",
        worker_pid=parsed["worker_pid"],
        output_file=parsed["output_file"],
        result_file=parsed["output_file"] or None,
        output_text=f"{proc.stdout}\n{proc.stderr}".strip(),
        log_file=str(LOG_FILE),
    )
    normalized["dispatch_stdout"] = proc.stdout.strip()
    normalized["dispatch_stderr"] = proc.stderr.strip()
    normalized["dispatch_exit_code"] = proc.returncode
    normalized["completion_artifact"] = str(artifact_path)
    if normalized["status"] in {"dispatched", "already_running", "failed"}:
        write_completion_artifact(artifact_path, normalized)
    return normalized


def pending_report_shell(snapshot_kind: str, target_date: str) -> dict[str, Any]:
    if snapshot_kind == "performance_tuning":
        return {
            "date": target_date,
            "metrics": {},
            "cards": [],
            "watch_items": [],
            "strategy_rows": [],
            "auto_comments": [],
            "breakdowns": {},
            "sections": {
                "swing_daily_summary": {},
                "judgment_gate": {},
                "holding_axis": {},
                "flow_bottleneck_lane": {},
                "observation_axis_coverage": [],
                "top_holding_slow": [],
                "top_gatekeeper_slow": [],
                "top_dual_persona_slow": [],
            },
            "meta": {},
        }
    if snapshot_kind == "post_sell_feedback":
        return {
            "date": target_date,
            "summary": {},
            "metrics": {},
            "insight": {},
            "exit_rule_tuning": [],
            "tag_tuning": [],
            "priority_actions": [],
            "soft_stop_forensics": {},
            "top_missed_upside": [],
            "top_good_exit": [],
            "meta": {},
        }
    if snapshot_kind == "trade_review":
        return {
            "date": target_date,
            "code": None,
            "scope": "entered",
            "since": None,
            "has_data": False,
            "metrics": {},
            "event_breakdown": [],
            "sections": {
                "recent_trades": [],
                "fill_quality_summary": {},
                "hard_stop_taxonomy": {},
            },
            "meta": {"warnings": [], "available_stocks": []},
        }
    if snapshot_kind == "holding_exit_observation":
        return {
            "date": target_date,
            "month_start": f"{target_date[:7]}-01" if target_date else "",
            "readiness": {},
            "cohorts": {},
            "exit_rule_quality": [],
            "trailing_continuation": {},
            "soft_stop_rebound": {},
            "same_symbol_reentry": {},
            "opportunity_cost": {},
            "load_distribution_evidence": {},
            "meta": {},
        }
    return {"date": target_date, "meta": {}}


def should_guard_stdin_heavy_build(target_date: str) -> bool:
    if os.getenv("MONITOR_SNAPSHOT_FROM_WRAPPER") == "1":
        return False
    if os.getenv("KORSTOCKSCAN_ALLOW_HEAVY_REPORT_DIRECT_BUILD") == "1":
        return False
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    if str(target_date or "").strip() != datetime.now().strftime("%Y-%m-%d"):
        return False
    for frame in inspect.stack()[1:8]:
        if frame.filename == "<stdin>":
            return True
    return False


def guard_stdin_heavy_build(
    *,
    snapshot_kind: str,
    target_date: str,
    fallback_snapshot: dict[str, Any] | None,
    request_details: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not should_guard_stdin_heavy_build(target_date):
        return None

    profile = HEAVY_SNAPSHOT_PROFILE_BY_KIND.get(snapshot_kind, "full")
    dispatch_info = dispatch_monitor_snapshot_job(
        target_date=target_date,
        profile=profile,
    )
    report = copy.deepcopy(
        fallback_snapshot or pending_report_shell(snapshot_kind, target_date)
    )
    meta = report.setdefault("meta", {})
    warnings = meta.get("warnings")
    if not isinstance(warnings, list):
        warnings = []
    warnings.append(
        f"{snapshot_kind} direct stdin build was auto-guarded. safe wrapper async dispatch status={dispatch_info.get('status','-')}"
    )
    if request_details:
        warnings.append(f"requested_filters={request_details}")
    meta.update(
        {
            "source": "snapshot" if fallback_snapshot else "pending",
            "guarded_heavy_builder": True,
            "guard_status": (
                "stale_snapshot_pending_refresh" if fallback_snapshot else "pending"
            ),
            "warnings": warnings,
            "async_dispatch": {
                "snapshot_kind": snapshot_kind,
                "profile": profile,
                "status": dispatch_info.get("status"),
                "worker_pid": dispatch_info.get("worker_pid"),
                "result_file": dispatch_info.get("result_file"),
                "completion_artifact": dispatch_info.get("completion_artifact"),
                "next_prompt_hint": dispatch_info.get("next_prompt_hint"),
            },
        }
    )
    report["pending"] = True
    return report
