"""Fetch remote KORStockScan scalping logs for a target date via SSH."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


DEFAULT_HOST = "songstockscan.ddns.net"
DEFAULT_USER = "windy80xyt"
DEFAULT_REMOTE_ROOT = "/home/windy80xyt/KORStockScan"
DEFAULT_LOCAL_ROOT = Path("/home/ubuntu/KORStockScan/tmp")


def _build_remote_paths(remote_root: str, target_date: str) -> list[str]:
    return [
        f"{remote_root}/logs/sniper_state_handlers_info.log",
        f"{remote_root}/logs/sniper_execution_receipts_info.log",
        f"{remote_root}/data/pipeline_events/pipeline_events_{target_date}.jsonl",
        f"{remote_root}/data/post_sell/post_sell_candidates_{target_date}.jsonl",
        f"{remote_root}/data/post_sell/post_sell_evaluations_{target_date}.jsonl",
    ]


def _build_optional_snapshot_paths(remote_root: str, target_date: str) -> list[str]:
    return [
        f"{remote_root}/data/report/monitor_snapshots/trade_review_{target_date}.json",
        f"{remote_root}/data/report/monitor_snapshots/post_sell_feedback_{target_date}.json",
        f"{remote_root}/data/report/monitor_snapshots/performance_tuning_{target_date}.json",
    ]


def _build_remote_tar_command(paths: list[str]) -> str:
    quoted_paths = " ".join(shlex.quote(path) for path in paths)
    return (
        "set -euo pipefail; "
        "tmpdir=$(mktemp -d); "
        'trap "rm -rf \\"$tmpdir\\"" EXIT; '
        f"files=({quoted_paths}); "
        'for f in "${files[@]}"; do '
        '  if [ ! -f "$f" ]; then '
        '    echo "missing_remote_file:$f" >&2; '
        "    exit 2; "
        "  fi; "
        '  cp -p "$f" "$tmpdir/"; '
        "done; "
        'cd "$tmpdir" && tar -czf - .; '
    )


def _build_remote_tar_command_with_optional_snapshots(
    required_paths: list[str],
    optional_snapshot_paths: list[str],
) -> str:
    required = " ".join(shlex.quote(path) for path in required_paths)
    optional = " ".join(shlex.quote(path) for path in optional_snapshot_paths)
    return (
        "set -euo pipefail; "
        "tmpdir=$(mktemp -d); "
        'trap "rm -rf \\"$tmpdir\\"" EXIT; '
        f"required=({required}); "
        f"optional=({optional}); "
        'for f in "${required[@]}"; do '
        '  if [ ! -f "$f" ]; then '
        '    echo "missing_remote_file:$f" >&2; '
        "    exit 2; "
        "  fi; "
        '  cp -p "$f" "$tmpdir/"; '
        "done; "
        'for f in "${optional[@]}"; do '
        '  if [ -f "$f" ]; then '
        '    cp -p "$f" "$tmpdir/"; '
        "  fi; "
        "done; "
        'if [ -z "$(ls -A $tmpdir)" ]; then exit 3; fi; cd "$tmpdir" && tar -czf - .; '
    )


def fetch_remote_scalping_logs(
    *,
    target_date: str,
    host: str,
    user: str,
    remote_root: str,
    local_root: Path,
    include_snapshots_if_exist: bool = False,
    snapshot_only_on_live_failure: bool = False,
) -> dict[str, str]:
    output_dir = local_root / f"remote_{target_date}"
    output_dir.mkdir(parents=True, exist_ok=True)

    archive_path = output_dir / f"remote_scalping_{target_date}.tar.gz"
    remote_paths = _build_remote_paths(remote_root, target_date)
    if include_snapshots_if_exist:
        remote_tar_cmd = _build_remote_tar_command_with_optional_snapshots(
            remote_paths,
            _build_optional_snapshot_paths(remote_root, target_date),
        )
    else:
        remote_tar_cmd = _build_remote_tar_command(remote_paths)
    ssh_target = f"{user}@{host}"

    status = "ok"
    try:
        with archive_path.open("wb") as archive_file:
            subprocess.run(
                ["ssh", ssh_target, remote_tar_cmd],
                check=True,
                stdout=archive_file,
                stderr=subprocess.PIPE,
            )
    except subprocess.CalledProcessError as e:
        # stderr 출력
        if e.stderr:
            sys.stderr.buffer.write(e.stderr)
        allow_fallback = False
        if snapshot_only_on_live_failure:
            if e.returncode == 1:
                stderr_output = e.stderr.decode() if e.stderr else ""
                if "file changed as we read it" in stderr_output:
                    allow_fallback = True
                else:
                    # cp 실패 등 다른 오류
                    allow_fallback = False
            # exit code 2 또는 다른 코드는 fallback 불허
        if allow_fallback:
            # fallback to snapshot-only
            print(
                f"[WARNING] live copy failed due to file changed as we read it, falling back to snapshot-only",
                file=sys.stderr,
            )
            snapshot_only_cmd = _build_remote_tar_command_with_optional_snapshots(
                [],
                _build_optional_snapshot_paths(remote_root, target_date),
            )
            with archive_path.open("wb") as archive_file:
                subprocess.run(
                    ["ssh", ssh_target, snapshot_only_cmd],
                    check=True,
                    stdout=archive_file,
                    stderr=subprocess.PIPE,
                )
            status = "partial_snapshot_only"
        else:
            raise

    subprocess.run(
        ["tar", "-xzf", str(archive_path), "-C", str(output_dir)],
        check=True,
    )

    return {
        "date": target_date,
        "archive_path": str(archive_path),
        "output_dir": str(output_dir),
        "status": status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch remote scalping logs via SSH.")
    parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD format.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--remote-root", default=DEFAULT_REMOTE_ROOT)
    parser.add_argument("--local-root", default=str(DEFAULT_LOCAL_ROOT))
    parser.add_argument(
        "--include-snapshots-if-exist",
        action="store_true",
        help="Also fetch trade_review/post_sell_feedback/performance_tuning snapshots if present.",
    )
    parser.add_argument(
        "--snapshot-only-on-live-failure",
        action="store_true",
        help="If live file copy fails, fallback to fetching only snapshot JSONs.",
    )
    args = parser.parse_args()

    result = fetch_remote_scalping_logs(
        target_date=args.date,
        host=args.host,
        user=args.user,
        remote_root=args.remote_root,
        local_root=Path(args.local_root),
        include_snapshots_if_exist=args.include_snapshots_if_exist,
        snapshot_only_on_live_failure=args.snapshot_only_on_live_failure,
    )
    print(
        f"[REMOTE_FETCH] date={result['date']} "
        f"archive={result['archive_path']} output_dir={result['output_dir']} "
        f"status={result['status']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
