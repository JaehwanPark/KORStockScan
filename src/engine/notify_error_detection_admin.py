"""Send admin Telegram notices for standalone error detection runs."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import time
from pathlib import Path
from urllib import parse, request

from src.utils.constants import CONFIG_PATH, DEV_PATH, PROJECT_ROOT

DEFAULT_STATE_FILE = PROJECT_ROOT / "tmp" / "error_detection_telegram_notify_state.json"

from src.engine.monitoring.semantic_incident_contract import (
    STAGE_HOOKS, fingerprint as semantic_fingerprint, reconcile, migrate_holding_gap_incidents,
    bound_observation,
)

SEMANTIC_ALERT_STAGES = frozenset(STAGE_HOOKS)


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
    # A damaged/partial report must not become an empty successful observation.
    limit = 32 * 1024 * 1024
    if path.is_symlink() or path.stat().st_size > limit:
        raise ValueError("notifier_report_untrusted")
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        raw = handle.read(limit + 1)
        after = os.fstat(handle.fileno())
    identity = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)
    if len(raw) > limit or identity(before) != identity(after) or identity(after) != identity(path.stat()):
        raise ValueError("notifier_report_changed")
    payload = json.loads(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("notifier_report_contract_invalid")
    return payload


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    if path.is_symlink() or path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("notifier_state_untrusted")
    with path.open("rb") as handle:
        raw = handle.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("notifier_state_oversize")
    payload = json.loads(raw)
    if not isinstance(payload, dict) or not isinstance(payload.get("semantic_incidents", {}), dict):
        raise ValueError("notifier_state_contract_invalid")
    return payload


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _is_alert_result(item: dict) -> bool:
    severity = str(item.get("severity") or "").lower()
    if severity == "fail":
        return True
    return (
        severity == "warning"
        and str(item.get("detector_id") or "") == "kiwoom_auth_8005_restart"
    )


def _semantic_source_matches(report, item, value):
    if value.get('source_date') == report.get('target_date'):
        return True
    bindings = (item.get('details') or {}).get('semantic_source_bindings') or []
    if any(isinstance(binding, dict)
           and binding.get('as_of_date') == report.get('target_date')
           and all(binding.get(key) == value.get(key) for key in (
               'source_date', 'target_date', 'stage', 'generation', 'status'))
           for binding in bindings):
        return True
    if value.get('stage') != 'entry_cancel_wait_tuning':
        return False
    observed = (item.get('details') or {}).get('entry_cancel_wait_result_semantics') or {}
    execution = observed.get('execution') or {}
    try:
        from datetime import date, timedelta
        previous = (date.fromisoformat(report['target_date']) - timedelta(days=1)).isoformat()
    except (KeyError, TypeError, ValueError):
        return False
    return (value.get('source_date') == previous == observed.get('source_date') == execution.get('source_date')
            and execution.get('status') in {'running', 'producers_completed', 'succeeded', 'failed'}
            and bool(execution.get('run_id')))


def _alert_results(report: dict) -> list[dict]:
    results = report.get("results")
    if not isinstance(results, list):
        return []
    alerts = []
    for item in results:
        if not isinstance(item, dict):
            continue
        if _is_alert_result(item):
            alerts.append(item)
        if item.get("detector_id") != "artifact_freshness":
            continue
        for value in (item.get("details") or {}).get("semantic_alerts", []):
            if (not isinstance(value, dict) or not _semantic_source_matches(report, item, value)
                or value.get("stage") not in SEMANTIC_ALERT_STAGES
                or value.get("status") in {"not_assessed", "historical_diagnostic", "off", "future_due", "retired"}
                or (value.get("status") == "unobservable" and not value.get("expected_overdue"))
                or not value.get("reason") or not value.get("owner")):
                continue
            if value.get('source_gap_identity') is not None:
                observed, bound = bound_observation(item.get('details') or {}, value, report.get('target_date'))
                if (not bound or observed.get('native_validated') is not True
                        or observed.get('observation_complete') is not True
                        or observed.get('report_sha256') != value.get('generation')
                        or observed.get('status') != value.get('status')
                        or observed.get('source_date') != value.get('source_date')
                        or observed.get('target_date') != value.get('target_date')
                        or observed.get('source_gap_identity') != value['source_gap_identity']):
                    value = {k: v for k, v in value.items() if k != 'source_gap_identity'}
            alerts.append({"detector_id": "artifact_freshness", "severity": "warning",
                "summary": value["reason"], "semantic_incident": value,
                "recommended_action": f"{value['owner']}: {value.get('closure_test', '')}"})
    return alerts


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


def _normalize_incident_summary(value: object) -> str:
    text = " ".join(str(value or "").split()).lower()
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}t\S+", "<timestamp>", text)
    text = re.sub(r"(?<![a-z])[-+]?\d+(?:\.\d+)?", "<n>", text)
    return text


def _incident_fingerprint(item: dict) -> str:
    semantic = item.get("semantic_incident")
    if isinstance(semantic, dict):
        return semantic_fingerprint(semantic)
    payload = {
        "detector_id": str(item.get("detector_id") or ""),
        "severity": str(item.get("severity") or "").lower(),
        "summary_class": _normalize_incident_summary(item.get("summary")),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _write_active_incident_state(
    state_file: Path,
    state: dict,
    *,
    fingerprints: list[str],
    report: dict,
    now: float,
) -> None:
    updated = dict(state)
    updated["active_incident_fingerprints"] = sorted(set(fingerprints))
    updated["active_incident_count"] = len(set(fingerprints))
    updated["last_seen_at_ts"] = now
    updated["last_seen_at"] = report.get("timestamp") or ""
    _write_state(state_file, updated)


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
        "- trading strategy runtime mutation: none",
    ]
    operational_mutations = report.get("operational_mutations")
    if isinstance(operational_mutations, list) and operational_mutations:
        lines.append(
            "- operational mutations: "
            + ", ".join(str(item) for item in operational_mutations)
        )
    for item in fail_results[:3]:
        detector_id = item.get("detector_id") or "-"
        severity = item.get("severity") or "-"
        summary = str(item.get("summary") or "-")[:400]
        action = str(item.get("recommended_action") or "-")[:200]
        lines.append(f"- {detector_id} [{severity}]: {summary}")
        semantic = item.get("semantic_incident")
        if isinstance(semantic, dict):
            lines.append(f"  source={semantic['source_date']} stage={semantic['stage']} scope={semantic.get('scope')}")
            if semantic.get('stage') == 'main_market_weakness_research':
                lines.append(f"  source_role={semantic.get('source_date_role')} latest_attempt_source={semantic.get('latest_attempt_source_date')} last_completed_source={semantic.get('last_completed_source_date')}")
                lines.append(f"  cumulative_through={semantic.get('research_through_date')} source_days={semantic.get('research_source_date_count')}")
            if semantic.get('bound_target_date') or semantic.get('next_due_target_date'):
                lines.append(f"  observed={semantic.get('observation_date')} bound_target={semantic.get('bound_target_date')} next_due={semantic.get('next_due_target_date')}")
            lines.append(f"  affected/eligible/total={semantic.get('affected')}/{semantic.get('eligible')}/{semantic.get('total')}")
            lines.append(f"  artifact={str(semantic.get('artifact'))[:250]} generation={semantic.get('generation')}")
        if action != "-":
            lines.append(f"  action: {action}")
    return "\n".join(lines)


def _notify_from_report_locked(
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

    try:
        report = _load_report(report_file)
    except (OSError, ValueError, TypeError):
        return "report_invalid"
    fail_results = _alert_results(report)
    now = time.time() if now_ts is None else now_ts
    state = _load_state(state_file)
    # A delayed detector result must not clear a newer failure or replace its
    # delivery receipt. Use the producer clock, never this sender's wall clock.
    if report.get('timestamp'):
        from datetime import datetime
        try:
            stamp = datetime.fromisoformat(report['timestamp'])
            if stamp.tzinfo is None:
                return 'report_clock_invalid'
            report_epoch = stamp.timestamp()
        except (ValueError, TypeError, OverflowError):
            return 'report_clock_invalid'
        if report_epoch < state.get('last_observation_epoch', 0):
            return 'stale_report'
        state['last_observation_epoch'] = report_epoch
    # Migrate delivered fingerprints without treating an owner rename as a
    # recurrence. Delivery receipts and unresolved observations remain distinct.
    details = next((r.get("details") or {} for r in report.get("results", [])
                    if isinstance(r, dict) and r.get("detector_id") == "artifact_freshness"), {})
    migration = migrate_holding_gap_incidents(state, details, report.get("target_date"))
    if "active_incident_fingerprints" in state:
        state["active_incident_fingerprints"] = [migration.get(k, k) for k in state["active_incident_fingerprints"]]
    delivered = set(state.get("notified_incident_fingerprints",
                              state.get("active_incident_fingerprints", [])))
    delivered = {migration.get(k, k) for k in delivered}
    if "notified_incident_fingerprints" in state:
        state["notified_incident_fingerprints"] = sorted(delivered)
    state = reconcile(state, details, report.get("target_date"),
        [r["semantic_incident"] for r in fail_results if isinstance(r.get("semantic_incident"), dict)],
        source_matches=lambda i: _semantic_source_matches(report, {"details": details}, i))
    unresolved = state["semantic_incidents"]
    if not fail_results:
        state["notified_incident_fingerprints"] = sorted(delivered.intersection(unresolved))
        _write_active_incident_state(state_file, state, fingerprints=list(unresolved), report=report, now=now)
        return "no_alert"

    sig = _signature(report, fail_results)
    fingerprinted_results = [
        (_incident_fingerprint(item), item) for item in fail_results
    ]
    current_fingerprints = [fingerprint for fingerprint, _ in fingerprinted_results]
    current_fingerprints.extend(unresolved)
    previous_fingerprints = delivered
    if previous_fingerprints:
        new_results = [
            item
            for fingerprint, item in fingerprinted_results
            if fingerprint not in previous_fingerprints
        ]
        if not new_results:
            _write_active_incident_state(
                state_file,
                state,
                fingerprints=current_fingerprints,
                report=report,
                now=now,
            )
            return "duplicate_incident"
    else:
        new_results = fail_results

    # Backward-compatible cooldown for pre-fingerprint state and a narrow
    # protection against duplicated invocations racing before state promotion.
    last_sig = str(state.get("signature") or "")
    last_ts = float(state.get("sent_at_ts") or 0.0)
    if (
        "active_incident_fingerprints" not in state
        and sig == last_sig
        and now - last_ts < cooldown_sec
    ):
        return "cooldown"

    token, admin_id = _load_telegram_config()
    if not token or not admin_id:
        _write_state(state_file, state)
        return "missing_config"

    # Persist each successfully delivered batch; retry only undisplayed incidents.
    try:
        for offset in range(0, len(new_results), 3):
            message = _build_message(report, new_results[offset:offset + 3], mode=mode, log_file=log_file)
            _send_telegram(token, admin_id, message)
            delivered.update(_incident_fingerprint(item) for item in new_results[offset:offset + 3])
            state['notified_incident_fingerprints'] = sorted(delivered)
            _write_state(state_file, state)
    except Exception:
        state["last_delivery_status"] = "failed_retryable"
        _write_state(state_file, state)
        raise
    _write_state(
        state_file,
        {
            **state,
            "signature": sig,
            "active_incident_fingerprints": sorted(set(current_fingerprints)),
            "active_incident_count": len(set(current_fingerprints)),
            "notified_incident_fingerprints": sorted(
                delivered.intersection(current_fingerprints)
                | {fingerprint for fingerprint, _ in fingerprinted_results}),
            "last_delivery_status": "sent",
            "sent_at_ts": now,
            "sent_at": report.get("timestamp") or "",
            "last_seen_at_ts": now,
            "last_seen_at": report.get("timestamp") or "",
            "mode": mode,
            "fail_count": len(new_results),
        },
    )
    return "sent"


def notify_from_report(report_file: Path, *, mode: str, log_file: str,
                       state_file: Path = DEFAULT_STATE_FILE, cooldown_sec: int = 600,
                       now_ts: float | None = None) -> str:
    """Serialize only notifier state, including direct CLI invocations."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.with_suffix(state_file.suffix + ".lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return "state_busy"
        try:
            _load_state(state_file)
        except (OSError, ValueError, TypeError):
            # Preserve damaged original bytes; a blank state would invent recovery.
            return "state_invalid"
        return _notify_from_report_locked(report_file, mode=mode, log_file=log_file,
            state_file=state_file, cooldown_sec=cooldown_sec, now_ts=now_ts)


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
