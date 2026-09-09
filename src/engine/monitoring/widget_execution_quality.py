"""Read-only exact widget execution incidents shared by existing policy producers.

No broker calls, policy writes or new runtime authority. Event counts remain
diagnostic; an exact later full-fill receipt can resolve a failed submit intent.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date, datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

CLEAN_DATE = date(2026, 6, 5)
DEFAULT_EVENT_DIR = Path("data/report/widget_signal_auto_trade_events")
FAILURES = {
    "order_submit_failed",
    "order_submit_ambiguous",
    "buy_cancel_terminal_failure",
    "sell_terminal_failure",
    "take_profit_cancel_terminal_failure",
    "take_profit_terminal_failure",
}
SESSIONS = {"KRX_REGULAR", "NXT_PREMARKET", "NXT_AFTERMARKET"}
EXECUTION_OWNER = "operator_directed_widget_auto_trade_v1"


def _custody_projection(incidents, *, symbol, target_date, registry_path):
    """Read a validated journal; project only exact fully flat manual custody.

    This closes exposure, not a successful target order or strategy profit.
    No registry/canonical event file is mutated and no broker call is made.
    """
    from src.trading.order.owner_custody_registry import (
        DEFAULT_REGISTRY_PATH,
        REGISTRY_SCHEMA,
        OrderOwnerRegistry,
    )

    path = Path(registry_path) if registry_path is not None else DEFAULT_REGISTRY_PATH
    audit = {
        "status": "not_present",
        "path": str(path),
        "projected_count": 0,
        "runtime_effect": False,
        "actual_order_submitted": False,
    }
    if not path.exists():
        return audit
    try:
        raw = path.read_bytes()
        events, previous_hash = [], "0" * 64
        for line in raw.decode().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            expected = hashlib.sha256(
                previous_hash.encode("ascii") + OrderOwnerRegistry._canonical(row)
            ).hexdigest()
            if (
                row.get("schema") != REGISTRY_SCHEMA
                or row.get("previous_hash") != previous_hash
                or row.get("event_hash") != expected
            ):
                raise ValueError("registry_chain_invalid")
            previous_hash = expected
            stamp = _timestamp(row.get("observed_at_kst"))
            if stamp is None:
                raise ValueError("registry_timestamp_invalid")
            if stamp.astimezone(ZoneInfo("Asia/Seoul")).date() <= target_date:
                events.append(row)
        audit.update(
            status="verified_read_only",
            source_sha256=hashlib.sha256(raw).hexdigest(),
            asof_tail_hash=events[-1]["event_hash"] if events else None,
        )
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
        audit["status"] = "registry_source_gap"
        return audit
    state = OrderOwnerRegistry._state(events)
    for incident in incidents.values():
        if (
            incident["status"] != "unresolved"
            or incident["identity_status"] != "exact"
            or incident["order_role"] not in {"TAKE_PROFIT_SELL", "FINAL_EXIT_SELL"}
        ):
            continue
        parent = incident["parent_signal_id"]
        matching = [
            r
            for r in state.values()
            if r.get("symbol") == symbol
            and r.get("owner_type") == "widget_auto_trade"
            and str(r.get("owner_id") or "").startswith(f"widget_auto_trade:{symbol}:")
            and r.get("position_id") == f"{r.get('owner_id')}:{parent}"
        ]
        identities = {
            (r.get("account_key"), r.get("owner_id"), r.get("position_id"))
            for r in matching
        }
        if len(identities) != 1 or not all(all(identity) for identity in identities):
            continue
        last_failure = _timestamp(incident["last_failure_at"])
        manual = [
            r
            for r in matching
            if r.get("event") == "MANUAL_EXIT_RECONCILED"
            and r.get("execution_owner_type") == "manual_operator"
            and r.get("state") == "ORDER_TERMINAL"
            and r.get("side") == "SELL"
            and r.get("action") == "NEW"
            and _number(r.get("filled_qty")) > 0
            and _number(r.get("quantity")) == _number(r.get("filled_qty"))
            and _number(r.get("fill_amount")) > 0
            and len(str(r.get("manual_exit_evidence_sha256") or "")) == 64
            and all(
                c in "0123456789abcdef"
                for c in str(r.get("manual_exit_evidence_sha256") or "")
            )
            and str(r.get("broker_order_no") or "").isdigit()
            and len(str(r.get("broker_order_no") or "")) == 7
            and last_failure
            and _timestamp(r.get("observed_at_kst")) > last_failure
        ]
        exposure = [
            r
            for r in matching
            if r.get("action") == "NEW"
            and not (
                r.get("state") == "INTENT_REJECTED"
                and not r.get("broker_order_no")
                and r.get("filled_qty") in (None, 0)
                and r.get("fill_amount") in (None, 0)
            )
        ]
        if (
            not manual
            or not exposure
            or any(
                r.get("state") != "ORDER_TERMINAL"
                or r.get("side") not in {"BUY", "SELL"}
                or type(r.get("filled_qty")) is not int
                or type(r.get("quantity")) is not int
                or not 0 <= r["filled_qty"] <= r["quantity"]
                or r["filled_qty"] > 0
                and _number(r.get("fill_amount")) <= 0
                for r in exposure
            )
        ):
            continue
        buys = sum(
            _number(r.get("filled_qty")) for r in exposure if r.get("side") == "BUY"
        )
        sells = sum(
            _number(r.get("filled_qty")) for r in exposure if r.get("side") == "SELL"
        )
        if buys <= 0 or sells != buys:
            continue
        incident.update(
            status="resolved_exact_manual_custody_flat",
            recovery_role="custody_closed_not_target_execution_success",
            recovery_receipt_hashes=[r["event_hash"] for r in manual],
            recovery_order_nos=[r["broker_order_no"] for r in manual],
            recovered_at=max(r["observed_at_kst"] for r in manual),
        )
        audit["projected_count"] += 1
    return audit


def event_session(row: dict) -> str | None:
    for key in (
        "execution_policy_session",
        "market_session",
        "session_bucket",
        "session",
    ):
        value = str(row.get(key) or "").upper()
        if value in SESSIONS:
            return value
    for key in ("parent_entry_signal_id", "signal_id"):
        for session in sorted(SESSIONS):
            if f":{session}:" in str(row.get(key) or ""):
                return session
    if row.get("market_venue") == "KRX":
        return "KRX_REGULAR"
    if row.get("market_venue") == "NXT":
        stamp = _timestamp(row.get("observed_at"))
        if stamp:
            clock = stamp.astimezone(ZoneInfo("Asia/Seoul")).time()
            if clock < time(9):
                return "NXT_PREMARKET"
            if clock >= time(15, 30):
                return "NXT_AFTERMARKET"
    return None


def _timestamp(value: Any) -> datetime | None:
    try:
        stamp = datetime.fromisoformat(str(value))
        return stamp if stamp.tzinfo is not None else None
    except ValueError:
        return None


def _number(value: Any) -> int:
    if isinstance(value, bool) or isinstance(value, float) and not value.is_integer():
        return 0
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return 0


def _role(row: dict) -> str:
    event = str(row.get("event_type") or "")
    if event == "entry_episode_closed_submit_rejected":
        return "ENTRY_BUY"
    if "cancel_terminal" in event:
        return "BUY_CANCEL" if event.startswith("buy_") else "TAKE_PROFIT_CANCEL"
    if event == "take_profit_terminal_failure":
        return "TAKE_PROFIT_SELL"
    if event == "sell_terminal_failure":
        return "FINAL_EXIT_SELL"
    return str(row.get("order_role") or row.get("side") or "UNKNOWN")


def load_execution_incidents(
    symbol: str,
    *,
    target_date: date,
    session: str | None = None,
    event_dir: Path = DEFAULT_EVENT_DIR,
    custody_registry_path: Path | None = None,
) -> dict:
    incidents: dict[tuple, dict] = {}
    orders: dict[tuple, dict] = {}
    source_hashes: dict[str, str] = {}
    gaps = 0
    seen: set[str] = set()
    duplicate_count = 0
    same_day_failures = 0
    rows: list[tuple[date, int, dict]] = []
    for path in sorted(event_dir.glob("widget_signal_auto_trade_events_*.jsonl")):
        try:
            day = datetime.strptime(path.stem.rsplit("_", 1)[-1], "%Y%m%d").date()
        except ValueError:
            continue
        if not CLEAN_DATE <= day <= target_date:
            continue
        try:
            raw = path.read_bytes()
            lines = raw.decode("utf-8").splitlines()
        except (OSError, UnicodeError):
            gaps += 1
            continue
        source_hashes[str(path)] = hashlib.sha256(raw).hexdigest()
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                gaps += 1
                continue
            if not isinstance(row, dict):
                gaps += 1
                continue
            if str(row.get("symbol") or "") != symbol:
                continue
            row_owner = str(
                row.get("execution_authority") or row.get("decision_authority") or ""
            )
            if row_owner and row_owner != EXECUTION_OWNER:
                continue
            fingerprint = json.dumps(row, sort_keys=True, ensure_ascii=True)
            if fingerprint in seen:
                duplicate_count += 1
                continue
            seen.add(fingerprint)
            stamp = _timestamp(row.get("observed_at"))
            if stamp and stamp.astimezone(ZoneInfo("Asia/Seoul")).date() != day:
                gaps += 1
                continue
            scoped = event_session(row)
            if session is not None and scoped != session:
                if scoped is not None or row.get("event_type") not in FAILURES:
                    continue
            rows.append((day, line_number, row))
    # File order is authoritative for equal/missing timestamps. An out-of-order
    # or unscoped success never proves recovery of an earlier exact failure.
    for day, line_number, row in rows:
        event = str(row.get("event_type") or "")
        parent = str(row.get("parent_entry_signal_id") or row.get("signal_id") or "")
        parent = parent.split(":TP:", 1)[0]
        policy = str(row.get("execution_policy_id") or "")
        scope = event_session(row)
        role = _role(row)
        owner = str(
            row.get("execution_authority") or row.get("decision_authority") or ""
        )
        cancel_order_no = (
            str(row.get("order_no") or "") if role.endswith("_CANCEL") else ""
        )
        exact = bool(
            (parent or cancel_order_no)
            and policy
            and scope
            and role != "UNKNOWN"
            and owner
        )
        key = (owner, symbol, scope, policy, parent, role)
        if cancel_order_no:
            key = (owner, symbol, scope, policy, cancel_order_no, role)
        stamp = _timestamp(row.get("observed_at"))
        if event in FAILURES:
            same_day_failures += day == target_date
            if not exact:
                key += (day.isoformat(), line_number)
            incident = incidents.setdefault(
                key,
                {
                    "owner": owner,
                    "symbol": symbol,
                    "session": scope,
                    "policy_id": policy,
                    "parent_signal_id": parent,
                    "order_role": role,
                    "order_no": str(row.get("order_no") or ""),
                    "identity_status": "exact" if exact else "source_gap",
                    "first_source_date": day.isoformat(),
                    "failure_event_count": 0,
                    "failed_submit_attempt_count": 0,
                    "terminal_failure_event_count": 0,
                    "max_requested_qty": 0,
                    "status": "unresolved",
                    "last_failure_at": None,
                    "unresolved_ambiguity_seen": False,
                },
            )
            incident["failure_event_count"] += 1
            incident["failed_submit_attempt_count"] += event.startswith("order_submit_")
            incident["terminal_failure_event_count"] += not event.startswith(
                "order_submit_"
            )
            incident["max_requested_qty"] = max(
                incident["max_requested_qty"], _number(row.get("requested_qty"))
            )
            previous_stamp = _timestamp(incident.get("last_failure_at"))
            incident["last_failure_at"] = (
                max(stamp, previous_stamp).isoformat()
                if stamp and previous_stamp
                else stamp.isoformat() if stamp else None
            )
            incident["status"] = "unresolved"
            incident["unresolved_ambiguity_seen"] |= (
                event == "order_submit_ambiguous" or row.get("ambiguous") is True
            )
            # A definite BUY rejection has no broker custody to recover. Keep
            # its same-day operational veto, but do not demand a future fill of
            # an order which was never accepted. Ambiguity and SELL failures
            # remain open; a later different signal is never their recovery.
            if (
                exact
                and role == "ENTRY_BUY"
                and event == "order_submit_failed"
                and row.get("ambiguous") is False
                and row.get("actual_order_submitted") is False
                and not row.get("order_no")
                and str(row.get("return_code") or "") not in {"", "0"}
                and not incident["unresolved_ambiguity_seen"]
            ):
                incident["status"] = "closed_definitive_rejection_no_order"
        order_no = str(row.get("order_no") or "")
        if order_no and row.get("actual_order_submitted") is True:
            submitted = _timestamp(row.get("submitted_at"))
            order_day = (
                submitted.astimezone(ZoneInfo("Asia/Seoul")).date()
                if submitted
                else row.get("trade_date") or day
            )
            order_key = (owner, str(order_day), symbol, scope, policy, order_no)
            prior_order = orders.get(order_key, {})
            orders[order_key] = {
                "side": row.get("side") or prior_order.get("side"),
                "order_role": role,
                "source_date": str(order_day),
                "event_type": event,
                "order_status": row.get("order_status")
                or prior_order.get("order_status"),
                "filled_qty": max(
                    _number(row.get("filled_qty")),
                    _number(prior_order.get("filled_qty")),
                ),
                "requested_qty": _number(
                    row.get("requested_qty", prior_order.get("requested_qty"))
                ),
            }
        prior = incidents.get(key) if exact else None
        previous_stamp = _timestamp(prior.get("last_failure_at")) if prior else None
        if (
            prior
            and stamp
            and previous_stamp
            and stamp > previous_stamp
            and event == "order_execution_reconciled"
            and order_no
            and row.get("actual_order_submitted") is True
            and row.get("order_status") == "FILLED"
            and _number(row.get("requested_qty")) > 0
            and _number(row.get("filled_qty")) == _number(row.get("requested_qty"))
            and _number(row.get("filled_qty")) >= prior["max_requested_qty"] > 0
            and row.get("remaining_qty") == 0
            and not isinstance(row.get("remaining_qty"), bool)
            and _number(row.get("fill_price")) > 0
        ):
            prior.update(
                status="resolved_exact_full_fill",
                recovery_order_no=order_no,
                recovered_at=stamp.isoformat(),
            )
        # A zero-fill confirmed cancellation closes only the BUY cancel
        # incident, never a SELL intent or partially filled inventory.
        cancel = incidents.get((owner, symbol, scope, policy, order_no, "BUY_CANCEL"))
        cancel_stamp = _timestamp(cancel.get("last_failure_at")) if cancel else None
        if (
            cancel
            and stamp
            and cancel_stamp
            and stamp > cancel_stamp
            and event == "order_execution_reconciled"
            and row.get("actual_order_submitted") is True
            and row.get("side") == "BUY"
            and row.get("order_status") == "CANCELLED"
            and row.get("filled_qty") == 0
            and row.get("remaining_qty") == 0
            and not isinstance(row.get("filled_qty"), bool)
            and not isinstance(row.get("remaining_qty"), bool)
        ):
            cancel.update(
                status="resolved_exact_zero_fill_cancel",
                recovered_at=stamp.isoformat(),
                recovery_order_no=order_no,
            )
    custody_projection = _custody_projection(
        incidents,
        symbol=symbol,
        target_date=target_date,
        registry_path=custody_registry_path,
    )
    unresolved = [item for item in incidents.values() if item["status"] == "unresolved"]
    return {
        "schema": "widget_execution_incidents_v1",
        "source_target_date": target_date.isoformat(),
        "symbol": symbol,
        "owner": EXECUTION_OWNER,
        "session": session,
        "source_hashes": source_hashes,
        "custody_projection": custody_projection,
        "source_gap_count": gaps,
        "duplicate_event_count": duplicate_count,
        "incident_count": len(incidents),
        "unresolved_incident_count": len(unresolved),
        "resolved_incident_count": sum(
            item["status"].startswith("resolved_exact_") for item in incidents.values()
        ),
        "same_day_failure_event_count": same_day_failures,
        "closed_rejected_no_order_count": sum(
            item["status"] == "closed_definitive_rejection_no_order"
            for item in incidents.values()
        ),
        "incidents": list(incidents.values()),
        "unique_order_count": len(orders),
        "unique_order_count_by_side": dict(
            Counter(str(item["side"] or "UNKNOWN") for item in orders.values())
        ),
        "target_date_unique_order_count_by_side": dict(
            Counter(
                str(item["side"] or "UNKNOWN")
                for item in orders.values()
                if item["source_date"] == target_date.isoformat()
            )
        ),
        "full_fill_order_count": sum(
            item["requested_qty"] > 0
            and item["requested_qty"] == item["filled_qty"]
            and item["order_status"] == "FILLED"
            for item in orders.values()
        ),
        "partial_fill_order_count": sum(
            0 < item["filled_qty"] < item["requested_qty"] for item in orders.values()
        ),
        "runtime_apply_allowed": not unresolved and not gaps and not same_day_failures,
        "status": (
            "SOURCE_GAP"
            if gaps
            else (
                "SAFETY_VETO"
                if unresolved or same_day_failures
                else "NO_UNRESOLVED_INCIDENT_OBSERVED"
            )
        ),
        "decision_authority": "execution_quality_real_only_safety_veto",
        "metric_role": "exact_execution_incident_attribution",
        "window_policy": "clean_baseline_to_source_date_unresolved_carry",
        "sample_floor": "one_exact_failure_or_recovery_receipt",
        "primary_decision_metric": "unresolved_incident_count",
        "source_quality_gate": "dated_owner_signal_policy_order_full_fill_identity",
        "forbidden_uses": [
            "profit_evidence",
            "broker_guard_bypass",
            "missing_events_as_execution_success",
        ],
        "runtime_effect": False,
    }
