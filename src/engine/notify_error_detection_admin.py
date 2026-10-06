"""Send admin Telegram notices for standalone error detection runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_state(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


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
                or value.get("stage") not in {"legacy_machine_report", "main_auxiliary_policy", "postclose_handoff", "entry_cancel_wait_tuning",
                    "episode_policy", "samsung_frozen_validation", "episode_startup"}
                or value.get("status") in {"not_assessed", "unobservable"}
                or not value.get("reason") or not value.get("owner")):
                continue
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
        return hashlib.sha256(json.dumps([semantic.get(k) for k in (
            "owner", "source_date", "target_date", "stage", "scope", "reason", "generation")], separators=(",", ":")).encode()).hexdigest()
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
            lines.append(f"  affected/eligible/total={semantic.get('affected')}/{semantic.get('eligible')}/{semantic.get('total')}")
            lines.append(f"  artifact={str(semantic.get('artifact'))[:250]} generation={semantic.get('generation')}")
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
    now = time.time() if now_ts is None else now_ts
    state = _load_state(state_file)
    semantic_state = state.get("semantic_incidents")
    semantic_state = semantic_state if isinstance(semantic_state, dict) else {}
    details = next((r.get("details") or {} for r in report.get("results", [])
                    if isinstance(r, dict) and r.get("detector_id") == "artifact_freshness"), {})
    names = {"legacy_machine_report": "machine_result_semantics",
             "main_auxiliary_policy": "auxiliary_result_semantics",
             "postclose_handoff": "postclose_handoff_semantics",
             "entry_cancel_wait_tuning": "entry_cancel_wait_result_semantics",
             "episode_policy": "episode_policy_semantics",
             "samsung_frozen_validation": "samsung_frozen_validation_semantics",
             "episode_startup": "episode_startup_semantics"}
    unresolved = {}
    history = list(state.get("historical_semantic_incidents") or [])
    for fingerprint, incident in semantic_state.items():
        if not isinstance(incident, dict):
            continue
        observed = next((r.get('semantics') or {} for r in details.get('semantic_observations', [])
                         if r.get('stage') == incident.get('stage')
                         and (r.get('semantics') or {}).get('source_date') == incident.get('source_date')),
                        details.get(names.get(incident.get("stage"))) or {})
        bound = any(b.get('as_of_date') == report.get('target_date')
                    and b.get('stage') == incident.get('stage')
                    and b.get('source_date') == incident.get('source_date')
                    for b in details.get('semantic_source_bindings', []) if isinstance(b, dict))
        native_day = incident.get('source_date') if bound else (observed.get("source_date") if incident.get("stage") == "entry_cancel_wait_tuning"
            and _semantic_source_matches(report, {"details":details}, incident)
            and (observed.get("execution") or {}).get("source_date") == observed.get("source_date")
            else report.get("target_date"))
        if incident.get("source_date") != native_day:
            history.append({**incident, "disposition": "historical_unrecovered"})
        elif (observed.get("source_date") != incident.get("source_date")
              or observed.get("status") not in {
                  "pass", "warning", "source_gap", "review_required",
                  "incumbent_carry", "candidate_selected", "done"}
              or not observed.get("report_sha256")
              or (incident.get("scope") not in {None, "report"}
                  and incident.get("scope") not in (observed.get("scopes") or {}))
              or (incident.get("stage") == "entry_cancel_wait_tuning"
                  and incident.get("reason") == "cancel_wait_consumer_projection_invalid"
                  and (observed.get("consumers") or {}).get("status") != "verified")
              or (incident.get("stage") == "entry_cancel_wait_tuning"
                  and incident.get("reason") in {"cancel_wait_execution_failed", "cancel_wait_completed_report_missing"}
                  and (observed.get("execution") or {}).get("command_status") != "succeeded")
              or incident.get("reason") in (observed.get("findings") or [])):
            unresolved[fingerprint] = incident
    for item in fail_results:
        if isinstance(item.get("semantic_incident"), dict):
            incoming = item['semantic_incident']
            keys = ('owner', 'source_date', 'target_date', 'stage', 'scope', 'reason')
            for fingerprint, previous in list(unresolved.items()):
                if all(previous.get(k) == incoming.get(k) for k in keys) and previous.get('generation') != incoming.get('generation'):
                    history.append({**previous, 'disposition': 'superseded_generation_unrecovered'})
                    del unresolved[fingerprint]
            unresolved[_incident_fingerprint(item)] = incoming
    state.update(semantic_incidents=dict(list(unresolved.items())[-128:]),
                 historical_semantic_incidents=history[-128:])
    if not fail_results:
        if state.get("active_incident_fingerprints"):
            _write_active_incident_state(
                state_file,
                state,
                fingerprints=list(unresolved),
                report=report,
                now=now,
            )
        return "no_alert"

    sig = _signature(report, fail_results)
    fingerprinted_results = [
        (_incident_fingerprint(item), item) for item in fail_results
    ]
    current_fingerprints = [fingerprint for fingerprint, _ in fingerprinted_results]
    current_fingerprints.extend(unresolved)
    previous_fingerprints = {
        str(value)
        for value in state.get("active_incident_fingerprints", [])
        if str(value)
    }
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
        return "missing_config"

    # Do not mark undisplayed incidents as notified. Persist only after every
    # bounded message succeeds; transport failure remains retryable.
    for offset in range(0, len(new_results), 3):
        message = _build_message(report, new_results[offset:offset + 3], mode=mode, log_file=log_file)
        _send_telegram(token, admin_id, message)
    _write_state(
        state_file,
        {
            **state,
            "signature": sig,
            "active_incident_fingerprints": sorted(set(current_fingerprints)),
            "active_incident_count": len(set(current_fingerprints)),
            "sent_at_ts": now,
            "sent_at": report.get("timestamp") or "",
            "last_seen_at_ts": now,
            "last_seen_at": report.get("timestamp") or "",
            "mode": mode,
            "fail_count": len(new_results),
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
