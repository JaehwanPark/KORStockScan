"""Send admin Telegram notices for standalone error detection runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from urllib import parse, request

from src.utils.constants import CONFIG_PATH, DEV_PATH, PROJECT_ROOT

DEFAULT_STATE_FILE = PROJECT_ROOT / "tmp" / "error_detection_telegram_notify_state.json"


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
    except OSError:
        return "", ""
    token = str(config.get("TELEGRAM_TOKEN") or "").strip()
    admin_id = str(config.get("ADMIN_ID") or "").strip()
    return token, admin_id


def _send_telegram(token: str, admin_id: str, message: str) -> None:
    data = parse.urlencode({"chat_id": admin_id, "text": message}).encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        response.read()


def _load_report(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_alert_result(item: dict) -> bool:
    severity = str(item.get("severity") or "").lower()
    if severity == "fail":
        return True
    return (
        severity == "warning"
        and str(item.get("detector_id") or "") == "kiwoom_auth_8005_restart"
    )


def _alert_results(report: dict) -> list[dict]:
    results = report.get("results")
    if not isinstance(results, list):
        return []
    return [
        item for item in results if isinstance(item, dict) and _is_alert_result(item)
    ]


def _fail_results(report: dict) -> list[dict]:
    return _alert_results(report)


def _signature(report: dict, fail_results: list[dict]) -> str:
    payload = {
        "summary_severity": report.get("summary_severity"),
        "alerts": [
            {
                "detector_id": item.get("detector_id"),
                "severity": item.get("severity"),
                "summary": item.get("summary"),
            }
            for item in fail_results
        ],
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _build_message(
    report: dict, fail_results: list[dict], *, mode: str, log_file: str
) -> str:
    timestamp = report.get("timestamp") or "-"
    lines = [
        "[KORStockScan] ERROR DETECTION ALERT",
        f"- mode: {mode}",
        f"- timestamp: {timestamp}",
        f"- alert_count: {len(fail_results)}",
        f"- log: {log_file}",
        "- runtime mutation: none",
    ]
    for item in fail_results[:5]:
        detector_id = item.get("detector_id") or "-"
        severity = item.get("severity") or "-"
        summary = item.get("summary") or "-"
        action = item.get("recommended_action") or "-"
        lines.append(f"- {detector_id} [{severity}]: {summary}")
        if action != "-":
            lines.append(f"  action: {action}")
    return "\n".join(lines)


def notify_from_report(
    report_file: Path,
    *,
    mode: str,
    log_file: str,
    state_file: Path = DEFAULT_STATE_FILE,
    cooldown_sec: int = 600,
    now_ts: float | None = None,
) -> str:
    if str(
        os.getenv("KORSTOCKSCAN_ERROR_DETECTION_TELEGRAM_NOTIFY_ENABLED", "true")
    ).lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return "disabled"

    report = _load_report(report_file)
    fail_results = _alert_results(report)
    if not fail_results:
        return "no_alert"

    now = time.time() if now_ts is None else now_ts
    sig = _signature(report, fail_results)
    state = _load_state(state_file)
    last_sig = str(state.get("signature") or "")
    last_ts = float(state.get("sent_at_ts") or 0.0)
    if sig == last_sig and now - last_ts < cooldown_sec:
        return "cooldown"

    token, admin_id = _load_telegram_config()
    if not token or not admin_id:
        return "missing_config"

    message = _build_message(report, fail_results, mode=mode, log_file=log_file)
    _send_telegram(token, admin_id, message)
    _write_state(
        state_file,
        {
            "signature": sig,
            "sent_at_ts": now,
            "sent_at": report.get("timestamp") or "",
            "mode": mode,
            "fail_count": len(fail_results),
        },
    )
    return "sent"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Notify admin for error detector failures."
    )
    parser.add_argument("--report-file", required=True)
    parser.add_argument("--mode", default="full")
    parser.add_argument("--log-file", default="logs/run_error_detection.log")
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE))
    parser.add_argument("--cooldown-sec", type=int, default=600)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    status = notify_from_report(
        Path(args.report_file),
        mode=args.mode,
        log_file=args.log_file,
        state_file=Path(args.state_file),
        cooldown_sec=max(0, int(args.cooldown_sec)),
    )
    print(f"[INFO] error detection Telegram notify status={status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
