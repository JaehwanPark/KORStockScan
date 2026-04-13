"""Readiness and collection checks for WATCHING 75 shadow canary."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.fetch_remote_scalping_logs import (
    DEFAULT_HOST,
    DEFAULT_LOCAL_ROOT,
    DEFAULT_REMOTE_ROOT,
    DEFAULT_USER,
    fetch_remote_scalping_logs,
)
from src.engine.watching_prompt_75_shadow_report import build_watching_prompt_75_shadow_report


SEOUL_TZ = ZoneInfo("Asia/Seoul")
PHASE_PRESETS = {
    "preopen": {
        "require_bot": True,
        "require_shadow_env": True,
        "require_pipeline_file": False,
        "max_pipeline_stale_min": None,
        "fetch_remote": False,
        "build_report": False,
    },
    "open_check": {
        "require_bot": True,
        "require_shadow_env": True,
        "require_pipeline_file": True,
        "max_pipeline_stale_min": 20,
        "fetch_remote": False,
        "build_report": False,
    },
    "midmorning": {
        "require_bot": True,
        "require_shadow_env": True,
        "require_pipeline_file": True,
        "max_pipeline_stale_min": 20,
        "fetch_remote": True,
        "build_report": True,
    },
    "postclose": {
        "require_bot": False,
        "require_shadow_env": True,
        "require_pipeline_file": True,
        "max_pipeline_stale_min": 90,
        "fetch_remote": True,
        "build_report": True,
    },
}


def _today_iso() -> str:
    return datetime.now(SEOUL_TZ).date().isoformat()


def _run_ssh_json(*, host: str, user: str, remote_root: str, target_date: str) -> dict[str, Any]:
    script = f"""
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

root = Path({remote_root!r})
pipeline_path = root / 'data' / 'pipeline_events' / f'pipeline_events_{target_date}.jsonl'

def cmd_ok(command: str) -> bool:
    return subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

bot_lines = subprocess.run(
    \"ps -ef | grep -E 'bot_main.py' | grep -v grep\",
    shell=True,
    text=True,
    capture_output=True,
)
bot_running = bot_lines.returncode == 0 and bool(bot_lines.stdout.strip())

try:
    tmux_running = cmd_ok('tmux has-session -t bot')
except Exception:
    tmux_running = False

shadow_env = {{
    'enabled': False,
    'min': None,
    'max': None,
}}
for line in bot_lines.stdout.splitlines():
    parts = line.split()
    if len(parts) < 2:
        continue
    pid = parts[1]
    try:
        raw = Path(f'/proc/{{pid}}/environ').read_bytes().decode('utf-8', errors='ignore')
    except Exception:
        continue
    env_map = {{}}
    for chunk in raw.split(chr(0)):
        if '=' in chunk:
            k, v = chunk.split('=', 1)
            env_map[k] = v
    if 'AI_WATCHING_75_PROMPT_SHADOW_ENABLED' in env_map:
        shadow_env = {{
            'enabled': str(env_map.get('AI_WATCHING_75_PROMPT_SHADOW_ENABLED', '')).lower() in {{'1', 'true', 'yes', 'y', 'on'}},
            'min': env_map.get('AI_WATCHING_75_PROMPT_SHADOW_MIN_SCORE'),
            'max': env_map.get('AI_WATCHING_75_PROMPT_SHADOW_MAX_SCORE'),
        }}
        break

pipeline = {{
    'exists': pipeline_path.exists(),
    'size_bytes': pipeline_path.stat().st_size if pipeline_path.exists() else 0,
    'mtime_iso': None,
    'stale_minutes': None,
    'total_events': 0,
    'entry_events': 0,
    'ai_confirmed': 0,
    'shadow_rows': 0,
    'buy_diverged': 0,
    'latest_event_at': None,
}}

if pipeline_path.exists():
    stat = pipeline_path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime)
    pipeline['mtime_iso'] = mtime.isoformat()
    pipeline['stale_minutes'] = round((datetime.now() - mtime).total_seconds() / 60.0, 1)
    with pipeline_path.open('r', encoding='utf-8') as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            pipeline['total_events'] += 1
            if str(row.get('pipeline') or '') == 'ENTRY_PIPELINE':
                pipeline['entry_events'] += 1
            stage = str(row.get('stage') or '')
            if stage == 'ai_confirmed':
                pipeline['ai_confirmed'] += 1
            if stage == 'watching_prompt_75_shadow':
                pipeline['shadow_rows'] += 1
                fields = dict(row.get('fields') or {{}})
                if str(fields.get('buy_diverged') or '').lower() == 'true':
                    pipeline['buy_diverged'] += 1
            emitted_at = str(row.get('emitted_at') or '')
            if emitted_at:
                pipeline['latest_event_at'] = emitted_at

print(json.dumps({{
    'remote_root': str(root),
    'target_date': {target_date!r},
    'bot_running': bot_running,
    'tmux_bot_session': tmux_running,
    'shadow_env': shadow_env,
    'pipeline': pipeline,
}}, ensure_ascii=False))
"""
    proc = subprocess.run(
        ["ssh", f"{user}@{host}", "python3", "-"],
        input=script,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(proc.stdout.strip())


def _evaluate_status(remote: dict[str, Any], preset: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    pipeline = dict(remote.get("pipeline") or {})
    shadow_env = dict(remote.get("shadow_env") or {})

    if preset.get("require_bot") and not bool(remote.get("bot_running")):
        failures.append("bot_main.py not running")
    if preset.get("require_bot") and not bool(remote.get("tmux_bot_session")):
        warnings.append("tmux bot session not detected")
    if preset.get("require_shadow_env") and not bool(shadow_env.get("enabled")):
        failures.append("shadow env not enabled in bot runtime")
    if preset.get("require_pipeline_file") and not bool(pipeline.get("exists")):
        failures.append("pipeline_events file missing")

    stale_limit = preset.get("max_pipeline_stale_min")
    stale_minutes = pipeline.get("stale_minutes")
    if stale_limit is not None and stale_minutes is not None and float(stale_minutes) > float(stale_limit):
        failures.append(f"pipeline_events stale ({stale_minutes}m > {stale_limit}m)")

    if bool(pipeline.get("exists")) and int(pipeline.get("entry_events") or 0) == 0:
        warnings.append("pipeline_events exists but ENTRY_PIPELINE rows are 0")
    if bool(pipeline.get("exists")) and int(pipeline.get("ai_confirmed") or 0) == 0:
        warnings.append("no ai_confirmed rows yet")
    if int(pipeline.get("ai_confirmed") or 0) > 0 and int(pipeline.get("shadow_rows") or 0) == 0:
        warnings.append("ai_confirmed exists but shadow_rows still 0")

    if failures:
        return "fail", failures, warnings
    if warnings:
        return "warning", failures, warnings
    return "ok", failures, warnings


def build_shadow_canary_check(
    *,
    target_date: str,
    phase: str,
    host: str,
    user: str,
    remote_root: str,
    local_root: Path,
    fetch_remote_enabled: bool | None = None,
    build_report_enabled: bool | None = None,
) -> dict[str, Any]:
    preset = dict(PHASE_PRESETS[phase])
    remote = _run_ssh_json(host=host, user=user, remote_root=remote_root, target_date=target_date)
    status, failures, warnings = _evaluate_status(remote, preset)

    do_fetch = preset["fetch_remote"] if fetch_remote_enabled is None else bool(fetch_remote_enabled)
    do_report = preset["build_report"] if build_report_enabled is None else bool(build_report_enabled)

    fetch_result: dict[str, Any] | None = None
    report_summary: dict[str, Any] | None = None
    if do_fetch:
        fetch_result = fetch_remote_scalping_logs(
            target_date=target_date,
            host=host,
            user=user,
            remote_root=remote_root,
            local_root=local_root,
            include_snapshots_if_exist=True,
            snapshot_only_on_live_failure=True,
        )
    if do_report and fetch_result:
        data_dir = Path(fetch_result["output_dir"]) / "data"
        report = build_watching_prompt_75_shadow_report(target_date, data_dir=data_dir, missed_report={"rows": []})
        report_summary = {
            "shadow_samples": int((report.get("metrics") or {}).get("shadow_samples", 0)),
            "buy_diverged_count": int((report.get("metrics") or {}).get("buy_diverged_count", 0)),
            "joined_missed_rows": int((report.get("metrics") or {}).get("joined_missed_rows", 0)),
            "score_band_distribution": list(report.get("score_band_distribution") or []),
        }

    return {
        "date": target_date,
        "phase": phase,
        "status": status,
        "failures": failures,
        "warnings": warnings,
        "recommended_window": phase,
        "remote": remote,
        "fetch": fetch_result,
        "report": report_summary,
        "checked_at": datetime.now(SEOUL_TZ).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="WATCHING 75 shadow canary readiness/collection check")
    parser.add_argument("--date", default=_today_iso())
    parser.add_argument("--phase", choices=sorted(PHASE_PRESETS.keys()), required=True)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--remote-root", default=DEFAULT_REMOTE_ROOT)
    parser.add_argument("--local-root", default=str(DEFAULT_LOCAL_ROOT))
    parser.add_argument("--fetch-remote", action="store_true")
    parser.add_argument("--no-fetch-remote", action="store_true")
    parser.add_argument("--build-report", action="store_true")
    parser.add_argument("--no-build-report", action="store_true")
    args = parser.parse_args()

    fetch_override = None
    if args.fetch_remote:
        fetch_override = True
    elif args.no_fetch_remote:
        fetch_override = False

    report_override = None
    if args.build_report:
        report_override = True
    elif args.no_build_report:
        report_override = False

    result = build_shadow_canary_check(
        target_date=args.date,
        phase=args.phase,
        host=args.host,
        user=args.user,
        remote_root=args.remote_root,
        local_root=Path(args.local_root),
        fetch_remote_enabled=fetch_override,
        build_report_enabled=report_override,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
