"""Send an admin-only Telegram notice after monitor snapshot completion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib import parse, request

from src.utils.constants import CONFIG_PATH, DEV_PATH


def _load_json_line(path: Path) -> dict:
    last_payload: dict = {}
    if not path.exists():
        return last_payload
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line.startswith("{") or not line.endswith("}"):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            last_payload = parsed
    return last_payload


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    with open(config_path, "r", encoding="utf-8") as handle:
        config = json.load(handle)
    token = str(config.get("TELEGRAM_TOKEN") or "").strip()
    admin_id = str(config.get("ADMIN_ID") or "").strip()
    return token, admin_id


def _build_message(payload: dict, *, target_date: str, profile: str, log_file: str) -> str:
    status = str(payload.get("status") or "success")
    if payload.get("skipped") or status == "skipped":
        reason = payload.get("reason") or "-"
        lock_file = payload.get("lock_file") or "-"
        lines = [
            "[KORStockScan] monitor snapshot skipped",
            f"- date: {target_date}",
            f"- profile: {profile}",
            f"- reason: {reason}",
            f"- lock_file: {lock_file}",
            f"- status: {status}",
            f"- started_at: {payload.get('started_at', '-')}",
            f"- finished_at: {payload.get('finished_at', '-')}",
            f"- duration_sec: {payload.get('duration_sec', '-')}",
            f"- log: {log_file}",
        ]
        return "\n".join(lines)

    snapshots = payload.get("snapshots")
    if not isinstance(snapshots, dict):
        snapshots = {}

    snapshot_kinds = [
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
            "status",
            "error",
            "error_kind",
        }
        and not key.startswith("server_comparison_")
    ]
    trend_max_dates = snapshots.get("trend_max_dates", "-")
    server_status = snapshots.get("server_comparison_status") or snapshots.get("server_comparison_error") or "-"
    error_kind = payload.get("error_kind") or "-"
    error_message = payload.get("error") or "-"

    lines = [
        "[KORStockScan] monitor snapshot complete",
        f"- date: {target_date}",
        f"- profile: {profile}",
        f"- status: {status}",
        f"- started_at: {payload.get('started_at', '-')}",
        f"- finished_at: {payload.get('finished_at', '-')}",
        f"- duration_sec: {payload.get('duration_sec', '-')}",
        f"- snapshot_count: {len(snapshot_kinds)}",
        f"- kinds: {', '.join(snapshot_kinds) if snapshot_kinds else '-'}",
        f"- trend_max_dates: {trend_max_dates}",
        f"- max_date_basis: {target_date}",
        f"- server_comparison: {server_status}",
        f"- io_delay_sec_per_stage: {payload.get('io_delay_sec_per_stage') or snapshots.get('io_delay_sec_per_stage', '-')}",
        f"- error_kind: {error_kind}",
        f"- error: {error_message}",
        f"- log: {log_file}",
    ]
    return "\n".join(lines)


def _send_telegram(token: str, admin_id: str, message: str) -> None:
    data = parse.urlencode({"chat_id": admin_id, "text": message}).encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        response.read()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Notify admin that monitor snapshot completed.")
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--result-file", required=True)
    parser.add_argument("--log-file", default="logs/run_monitor_snapshot.log")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = _load_json_line(Path(args.result_file))
    token, admin_id = _load_telegram_config()
    if not token or not admin_id:
        print("[WARN] monitor snapshot Telegram notice skipped: TELEGRAM_TOKEN or ADMIN_ID missing")
        return 0

    message = _build_message(
        payload,
        target_date=args.target_date,
        profile=args.profile,
        log_file=args.log_file,
    )
    _send_telegram(token, admin_id, message)
    print("[INFO] monitor snapshot Telegram admin notice sent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
