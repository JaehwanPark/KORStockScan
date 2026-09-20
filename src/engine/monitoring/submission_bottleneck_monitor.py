"""Observe Sentinel's exact machine funnel; notification has no trading authority."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.notify_error_detection_admin import (
    _load_state, _load_telegram_config, _send_telegram, _write_state,
)
from src.utils.constants import PROJECT_ROOT

SCHEMA = "submission_bottleneck_monitor_v1"
KST = ZoneInfo("Asia/Seoul")
# Diagnostic persistence only. Never used by a trading policy or guard.
WINDOW_SEC = 1800
GRACE_SEC = 600
PERSIST_SEC = 900
MIN_PROMOTIONS = 10


def stamp(value):
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed.replace(tzinfo=KST) if parsed.tzinfo is None else parsed.astimezone(KST)
    except (ValueError, TypeError):
        return None


def snapshot(events, as_of):
    """Reuse already loaded events and the existing identity/terminal owner."""
    from src.engine.buy_funnel_sentinel import (
        _machine_primary_entry_funnel, _is_machine_primary_event, _machine_primary_evaluation_key,
    )

    now = stamp(as_of)
    recent = [e for e in events if 0 <= (now - stamp(e.emitted_at)).total_seconds() <= 2700]
    funnel = _machine_primary_entry_funnel(recent)
    return {
        "schema": SCHEMA, "as_of": now.isoformat(),
        "latest_event_at": max((stamp(e.emitted_at) for e in recent), default=now - timedelta(days=1)).isoformat(),
        "identity_missing_events": funnel["evaluation_identity_missing_event_count"],
        "rows": [{k: r[k] for k in (
            "evaluation_key", "scanner_promotion_id", "stock_code", "effective_venue",
            "session_bucket", "policy_bundle_hash", "first_evaluated_at", "last_event_at",
            "mechanistic_action", "ai_screen_status", "broker_acceptance_observed",
            "final_guard_blocked", "final_state", "conflict_reasons", "source_invalid_decomposition",
        )} for r in funnel["evaluation_ledger"]],
        "missing_identity_evidence": sorted({hashlib.sha256(
            repr((e.emitted_at, e.stage, e.stock_code, e.record_id, sorted(e.fields.items()))).encode()
        ).hexdigest() for e in recent if _is_machine_primary_event(e)
            and not _machine_primary_evaluation_key(e)
            and GRACE_SEC <= (now - stamp(e.emitted_at)).total_seconds() <= WINDOW_SEC}),
    }


def evaluate(report, state, now):
    """Pure state transition. Old/stale evidence never triggers recovery or alerts."""
    now = stamp(now)
    source = report.get("submission_monitor") or {}
    as_of = stamp(source.get("as_of"))
    latest = stamp(source.get("latest_event_at"))
    today = now.date().isoformat()
    prior = state if state.get("date") == today and state.get("schema") == SCHEMA else {}
    incidents = dict(prior.get("incidents") or {})
    result = {"schema": SCHEMA, "date": today, "as_of": now.isoformat(),
              "runtime_effect": False, "status": "unobservable", "blocker": None,
              "notification_status": "idle",
              "incidents": incidents, "notification_pending": [], "scopes": {},
              "source_as_of": prior.get("source_as_of"),
              "last_notification_at": prior.get("last_notification_at")}
    if (report.get("target_date") != today or report.get("dry_run")
            or source.get("schema") != SCHEMA or not as_of or not latest
            or not 0 <= (now - as_of).total_seconds() <= 420
            or not 0 <= (now - latest).total_seconds() <= 600):
        result["blocker"] = "missing_stale_or_noncurrent_sentinel_evidence"
        return result
    if prior.get("source_as_of") and as_of <= stamp(prior["source_as_of"]):
        result["blocker"] = "duplicate_or_reversed_source_snapshot"
        return result
    result.update(status="observing", source_as_of=as_of.isoformat())
    groups = defaultdict(list)
    for row in source.get("rows", []):
        start = stamp(row.get("first_evaluated_at"))
        if start and 0 <= (now - start).total_seconds() <= 2700:
            scope = "|".join(str(row.get(k) or "missing") for k in (
                "effective_venue", "session_bucket", "policy_bundle_hash"))
            groups[scope].append(row)
    if not groups:
        result.update(status="unobservable", blocker="no_identified_machine_evaluation")
    for scope, all_rows in groups.items():
        rows = [r for r in all_rows if (now - stamp(r["first_evaluated_at"])).total_seconds() <= WINDOW_SEC]
        # Count each promotion once for scarcity, but retain exact attempts for gaps.
        parents = {}
        for row in sorted(rows, key=lambda r: r["first_evaluated_at"]):
            parents[(row["scanner_promotion_id"], row["stock_code"])] = row
        valid = [r for r in parents.values() if not r["conflict_reasons"] and r["mechanistic_action"] != "SOURCE_INVALID"]
        entered = [r for r in valid if r["mechanistic_action"] == "ENTER_NOW"]
        veto = [r for r in entered if r["ai_screen_status"] == "veto"]
        accepted = [r for r in rows if r["broker_acceptance_observed"]]
        gaps = [r for r in all_rows if (now - stamp(r["first_evaluated_at"])).total_seconds() >= GRACE_SEC
                and (r["conflict_reasons"] or r["mechanistic_action"] == "SOURCE_INVALID"
                     or r["final_state"].startswith("lineage_gap")
                     or r["final_state"] == "pending_broker_reconciliation"
                     or (r["ai_screen_status"] == "pass" and r["final_state"] == "pending"))]
        tests = {
            "source_or_submit_lineage_gap": (gaps, "structural_evidence", 240),
            "enter_now_scarcity": (valid if len(valid) >= MIN_PROMOTIONS and not entered else [], "review_required", PERSIST_SEC),
            "ai_veto_concentration": (veto if len(entered) >= MIN_PROMOTIONS and len(veto) / len(entered) >= .9 and not accepted else [], "review_required", PERSIST_SEC),
        }
        result["scopes"][scope] = {"unique_promotions": len(parents), "valid_promotions": len(valid),
            "enter_now": len(entered), "veto": len(veto), "accepted_attempts": len(accepted),
            "unresolved_attempts": len(gaps), "guard_blocked": sum(r["final_guard_blocked"] for r in rows)}
        for rule, (bad, category, persistence) in tests.items():
            key = hashlib.sha256(f"{scope}|{rule}".encode()).hexdigest()[:24]
            old = incidents.get(key, {})
            ids = sorted({r["evaluation_key"] for r in bad})
            if bad:
                first = old.get("first_seen", now.isoformat()) if old.get("status") in {"pending", "active"} else now.isoformat()
                # Ratios need new independent promotions, not repeated snapshots.
                identities = sorted({f'{r["scanner_promotion_id"]}|{r["stock_code"]}' for r in bad})
                new_support = bool(set(identities) - set(old.get("promotion_ids", [])))
                confirmed = bool(old) and (now - stamp(first)).total_seconds() >= persistence
                confirmed = confirmed and (category == "structural_evidence" or new_support or old.get("status") == "active")
                item = {"scope": scope, "rule": rule, "category": category, "first_seen": first,
                    "last_seen": now.isoformat(), "status": "active" if confirmed else "pending",
                    "evidence_ids": ids[:128], "promotion_ids": identities[:128],
                    "count": len(ids), "notified_status": old.get("notified_status"),
                    "examples": [{k: r.get(k) for k in ("stock_code", "evaluation_key", "final_state", "conflict_reasons", "source_invalid_decomposition")} for r in bad[:3]],
                    "owner": "buy_funnel_sentinel.machine_primary_entry_funnel",
                    "closure_test": "same attempt receives a consistent terminal; ratios recover on new valid promotions"}
                incidents[key] = item
            elif old and old.get("status") == "active":
                # Window expiration is not recovery. Require explicit closure evidence.
                old_ids = set(old.get("evidence_ids", []))
                resolved = {r["evaluation_key"] for r in all_rows if r["evaluation_key"] in old_ids
                    and not r["conflict_reasons"] and r["final_state"] in {"submit_pipeline_reached", "final_guard_blocked", "broker_rejected"}}
                healthy = bool(old_ids and old_ids <= resolved) if category == "structural_evidence" else bool(accepted and any(r["evaluation_key"] not in old_ids for r in accepted))
                if healthy:
                    incidents[key] = {**old, "status": "recovered", "last_seen": now.isoformat()}
            elif old and old.get("status") == "pending":
                incidents.pop(key, None)
    missing = source.get("missing_identity_evidence") or []
    key = "unbound_machine_identity"
    old = incidents.get(key, {})
    if missing:
        first = old.get("first_seen", now.isoformat()) if old.get("status") in {"pending", "active"} else now.isoformat()
        result["scopes"]["unbound"] = {"missing_identity_events": len(missing)}
        incidents[key] = {"scope": "unbound", "rule": "source_identity_missing",
            "category": "structural_evidence", "first_seen": first, "last_seen": now.isoformat(),
            "status": "active" if (now - stamp(first)).total_seconds() >= 240 else "pending",
            "count": len(missing), "evidence_ids": missing[:128], "examples": [],
            "notified_status": old.get("notified_status"),
            "owner": "ENTRY_PIPELINE machine producer identity",
            "closure_test": "new identified machine evaluations with no missing identity; old unbound rows remain unrepairable"}
    elif old and old.get("status") == "pending":
        incidents.pop(key, None)
    if source.get("identity_missing_events"):
        result["blocker"] = "machine_identity_missing_events"
        result["identity_missing_events"] = source["identity_missing_events"]
    # Absent scopes/stale sources retain incidents without asserting they resolved.
    result["notification_pending"] = [k for k, v in incidents.items()
        if v["status"] in {"active", "recovered"} and v.get("notified_status") != v["status"]
        and v["scope"] in result["scopes"]]
    return result


def notify(result, path, send=None):
    keys = result["notification_pending"]
    last = stamp(result.get("last_notification_at"))
    if last and (stamp(result["as_of"]) - last).total_seconds() < 300:
        result["notification_status"] = "cooldown"
        return
    if not keys:
        return
    messages = []
    for key in keys[:4]:
        item = result["incidents"][key]
        messages.append(f'{item["status"]}: {item["rule"]}\n{item["scope"]}\n근거 {item["count"]}건 / {item["category"]}\n' +
                        json.dumps(item.get("examples", [])[:1], ensure_ascii=False)[:350])
    message = "[제출병목 점검] 자동 매매 변경 없음\n" + "\n".join(messages) + f"\n근거: {path}\nCodex에서 원천과 제출 경로를 점검하세요."
    if send is None:
        try:
            token, admin = _load_telegram_config()
        except (OSError, ValueError):
            result["notification_status"] = "configuration_invalid"
            return
        if not token or not admin:
            result["notification_status"] = "configuration_missing"
            return
        send = lambda text: _send_telegram(token, admin, text)
    try:
        send(message[:4000])
    except Exception as exc:
        # Never leak a token-bearing HTTP exception into logs.
        result["notification_status"] = f"retry_required:{type(exc).__name__}"
        return
    for key in keys[:4]:
        result["incidents"][key]["notified_status"] = result["incidents"][key]["status"]
    result["notification_status"] = "sent"
    result["last_notification_at"] = result["as_of"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--notify", action="store_true")
    args = parser.parse_args()
    state_path = PROJECT_ROOT / "tmp/submission_bottleneck_monitor_state.json"
    output = PROJECT_ROOT / "data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json"
    try:
        if args.report.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("report_size_limit")
        report = json.loads(args.report.read_text())
        if not isinstance(report, dict):
            report = {}
    except (OSError, ValueError):
        report = {}
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        result = evaluate(report, _load_state(state_path), datetime.now(KST))
        if args.notify:
            notify(result, output)
        _write_state(state_path, result)
        _write_state(output, result)
        _write_state(output.with_name(f"submission_bottleneck_monitor_{result['date']}.json"), result)
    print(json.dumps({k: result.get(k) for k in ("status", "blocker", "notification_status")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
