"""Collect remote latency baseline snapshots via SSH."""

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
    DEFAULT_REMOTE_ROOT,
    DEFAULT_USER,
)

SEOUL_TZ = ZoneInfo("Asia/Seoul")
DEFAULT_LOCAL_ROOT = Path("/home/ubuntu/KORStockScan/tmp/remote_latency_baseline")


def _today_iso() -> str:
    return datetime.now(SEOUL_TZ).date().isoformat()


def _default_output_paths(local_root: Path, target_date: str, window: str, ts: str) -> tuple[Path, Path]:
    output_dir = local_root / target_date
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{target_date}_{window}_{ts}"
    return output_dir / f"{stem}.json", output_dir / f"{stem}.md"


def _build_remote_script(remote_root: str, target_date: str) -> str:
    return f"""
import json
import socket
import subprocess
from datetime import datetime
from pathlib import Path

root = Path({remote_root!r})
pipeline_path = root / 'data' / 'pipeline_events' / f'pipeline_events_{target_date}.jsonl'

bot_lines = subprocess.run(
    \"ps -ef | grep -E 'bot_main.py' | grep -v grep\",
    shell=True,
    text=True,
    capture_output=True,
)

bot_pids = []
for line in bot_lines.stdout.splitlines():
    parts = line.split()
    if len(parts) >= 2:
        bot_pids.append(parts[1])

pid = bot_pids[0] if bot_pids else ''

def read_cmd(command: str) -> list[str]:
    proc = subprocess.run(command, shell=True, text=True, capture_output=True)
    text = proc.stdout if proc.returncode == 0 else proc.stderr
    return [line.rstrip() for line in text.splitlines() if line.strip()]

latency_env = {{}}
if pid:
    try:
        raw = Path(f'/proc/{{pid}}/environ').read_bytes().decode('utf-8', errors='ignore')
    except Exception:
        raw = ''
    env_map = {{}}
    for chunk in raw.split(chr(0)):
        if '=' in chunk:
            k, v = chunk.split('=', 1)
            env_map[k] = v
    for key in [
        'KORSTOCKSCAN_LATENCY_CANARY_PROFILE',
        'KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS',
    ]:
        if key in env_map:
            latency_env[key] = env_map[key]

pipeline = {{
    'exists': pipeline_path.exists(),
    'size_bytes': pipeline_path.stat().st_size if pipeline_path.exists() else 0,
    'line_count': 0,
    'entry_pipeline_rows': 0,
    'latency_block_rows': 0,
    'latest_event_at': None,
}}
if pipeline_path.exists():
    with pipeline_path.open('r', encoding='utf-8') as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            pipeline['line_count'] += 1
            if str(row.get('pipeline') or '') == 'ENTRY_PIPELINE':
                pipeline['entry_pipeline_rows'] += 1
            if str(row.get('stage') or '') == 'latency_block':
                pipeline['latency_block_rows'] += 1
            emitted_at = str(row.get('emitted_at') or '')
            if emitted_at:
                pipeline['latest_event_at'] = emitted_at

payload = {{
    'collected_at': datetime.now().isoformat(),
    'hostname': socket.gethostname(),
    'remote_root': str(root),
    'target_date': {target_date!r},
    'bot_running': bool(pid),
    'bot_pid': pid,
    'tmux_bot_session': subprocess.run('tmux has-session -t bot', shell=True).returncode == 0,
    'latency_env': latency_env,
    'thread_snapshot': read_cmd(f'ps -L -p {{pid}} -o pid,tid,pcpu,pmem,etime,cmd | sed -n \"1,20p\"') if pid else [],
    'top_snapshot': read_cmd(f'top -b -n 1 -H -p {{pid}} | sed -n \"1,20p\"') if pid else [],
    'pipeline': pipeline,
}}
print(json.dumps(payload, ensure_ascii=False))
"""


def _run_ssh_json(*, host: str, user: str, remote_root: str, target_date: str) -> dict[str, Any]:
    proc = subprocess.run(
        ["ssh", f"{user}@{host}", "python3", "-"],
        input=_build_remote_script(remote_root, target_date),
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(proc.stdout.strip())


def _render_markdown(window: str, payload: dict[str, Any]) -> str:
    pipeline = dict(payload.get("pipeline") or {})
    latency_env = dict(payload.get("latency_env") or {})
    lines = [
        f"# Remote Latency Baseline / {window}",
        "",
        f"- collected_at: `{payload.get('collected_at', '')}`",
        f"- hostname: `{payload.get('hostname', '')}`",
        f"- bot_running: `{payload.get('bot_running', False)}`",
        f"- bot_pid: `{payload.get('bot_pid', '')}`",
        f"- tmux_bot_session: `{payload.get('tmux_bot_session', False)}`",
        f"- latency_profile: `{latency_env.get('KORSTOCKSCAN_LATENCY_CANARY_PROFILE', '')}`",
        f"- latency_max_ws_jitter_ms: `{latency_env.get('KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS', '')}`",
        f"- pipeline_exists: `{pipeline.get('exists', False)}`",
        f"- pipeline_line_count: `{pipeline.get('line_count', 0)}`",
        f"- entry_pipeline_rows: `{pipeline.get('entry_pipeline_rows', 0)}`",
        f"- latency_block_rows: `{pipeline.get('latency_block_rows', 0)}`",
        f"- latest_event_at: `{pipeline.get('latest_event_at', '')}`",
        "",
        "## Thread Snapshot",
        "",
        "```text",
    ]
    lines.extend(payload.get("thread_snapshot") or ["<empty>"])
    lines.extend([
        "```",
        "",
        "## Top Snapshot",
        "",
        "```text",
    ])
    lines.extend(payload.get("top_snapshot") or ["<empty>"])
    lines.extend([
        "```",
        "",
    ])
    return "\n".join(lines)


def collect_remote_latency_baseline(
    *,
    target_date: str,
    window: str,
    host: str,
    user: str,
    remote_root: str,
    local_root: Path,
    json_output: Path | None = None,
    markdown_output: Path | None = None,
) -> dict[str, Any]:
    ts = datetime.now(SEOUL_TZ).strftime("%Y%m%d_%H%M%S")
    if json_output is None or markdown_output is None:
        default_json, default_md = _default_output_paths(local_root, target_date, window, ts)
        json_output = json_output or default_json
        markdown_output = markdown_output or default_md
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)

    payload = _run_ssh_json(host=host, user=user, remote_root=remote_root, target_date=target_date)
    payload.update({
        "window": window,
        "status": "ok" if payload.get("bot_running") else "fail",
        "json_output": str(json_output),
        "markdown_output": str(markdown_output),
    })
    json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown_output.write_text(_render_markdown(window, payload), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect remote latency baseline snapshots")
    parser.add_argument("--date", default=_today_iso())
    parser.add_argument("--window", choices=["preopen", "midmorning", "afternoon"], required=True)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--remote-root", default=DEFAULT_REMOTE_ROOT)
    parser.add_argument("--local-root", default=str(DEFAULT_LOCAL_ROOT))
    parser.add_argument("--json-output")
    parser.add_argument("--markdown-output")
    args = parser.parse_args()

    result = collect_remote_latency_baseline(
        target_date=args.date,
        window=args.window,
        host=args.host,
        user=args.user,
        remote_root=args.remote_root,
        local_root=Path(args.local_root),
        json_output=Path(args.json_output) if args.json_output else None,
        markdown_output=Path(args.markdown_output) if args.markdown_output else None,
    )
    print(json.dumps({
        "date": result["target_date"],
        "window": result["window"],
        "status": result["status"],
        "bot_running": result["bot_running"],
        "bot_pid": result["bot_pid"],
        "pipeline_exists": result.get("pipeline", {}).get("exists", False),
        "pipeline_line_count": result.get("pipeline", {}).get("line_count", 0),
        "json_output": result["json_output"],
        "markdown_output": result["markdown_output"],
    }, ensure_ascii=False))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
