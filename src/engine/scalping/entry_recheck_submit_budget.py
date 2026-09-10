"""Durable reservations for the existing recheck accepted-order budget.

An arm consumes no submission budget. Reserve immediately before broker I/O;
only a definitive no-order rejection releases it. Unknown outcomes stay charged
across restart, and replaying the same reservation cannot send another order.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
import threading
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any

from src.engine.scalping.entry_recheck_policy import SCOPES, count
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto

DIRECTORY = DATA_DIR / "runtime" / "entry_recheck_submit_budget"
SCHEMA = "entry_recheck_submit_budget_v1"
_LOCK = threading.RLock()
_BOOTSTRAP_LOCK = threading.Lock()
_BOOTSTRAP_JOB: dict[str, Any] = {}


def _path(trade_date: str) -> Path:
    if date.fromisoformat(trade_date).isoformat() != trade_date:
        raise ValueError("invalid_budget_date")
    return DIRECTORY / f"{trade_date}.json"


def _validate(payload: Any, trade_date: str) -> dict[str, Any]:
    if (
        not isinstance(payload, dict)
        or payload.get("schema") != SCHEMA
        or payload.get("trade_date") != trade_date
    ):
        raise ValueError("invalid_budget_ledger")
    rows = payload.get("attempts")
    if not isinstance(rows, dict):
        raise ValueError("invalid_budget_attempts")
    for key, row in rows.items():
        if (
            not isinstance(key, str)
            or not key
            or not isinstance(row, dict)
            or row.get("status") not in {"reserved", "accepted", "rejected"}
            or not isinstance(row.get("code"), str)
            or not row["code"]
            or row.get("scope") not in SCOPES | {"legacy_unknown"}
            or (row["status"] == "accepted" and not row.get("broker_order_no"))
        ):
            raise ValueError("invalid_budget_attempt")
    return payload


def _load(path: Path, trade_date: str) -> dict[str, Any]:
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            return _validate(json.load(handle), trade_date)
    return {"schema": SCHEMA, "trade_date": trade_date, "attempts": {}}


def _write(path: Path, payload: dict[str, Any]) -> None:
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, allow_nan=False, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def _locked(path: Path):
    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.with_suffix(".lock").open("a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _charged(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in payload["attempts"].values() if row["status"] != "rejected"]


def observed_count(trade_date: str) -> int | None:
    """Advisory evaluation count. The final atomic reservation is authoritative."""
    try:
        path = _path(trade_date)
        with _locked(path):
            payload = _load(path, trade_date)
            if not path.exists():
                _bootstrap_legacy(payload, trade_date)
                _write(path, payload)
            return len(_charged(payload))
    except (OSError, ValueError, TypeError):
        return None


def observe_nonblocking(trade_date: str) -> dict[str, Any]:
    """Read committed advisory quota without scanning history on the live thread.

    Atomic replacement makes an unlocked read of an existing ledger sufficient
    for observation only. The final locked reservation remains authoritative.
    A missing ledger starts at most one background bootstrap for that path;
    pending/failed initialization is unknown, never an empty budget. Only one
    worker may run at a time, including across the trading-date boundary.
    """
    try:
        path = _path(trade_date)
        with path.open(encoding="utf-8") as handle:
            payload = _validate(json.load(handle), trade_date)
        return {"count": len(_charged(payload)), "status": "ready"}
    except FileNotFoundError:
        pass
    except (OSError, ValueError, TypeError):
        return {"count": None, "status": "ledger_invalid"}

    if not _BOOTSTRAP_LOCK.acquire(blocking=False):
        return {"count": None, "status": "bootstrap_pending"}
    try:
        job_path = str(path)
        if _BOOTSTRAP_JOB.get("path") == job_path:
            return {"count": None, "status": _BOOTSTRAP_JOB["status"]}
        if _BOOTSTRAP_JOB.get("status") == "bootstrap_pending":
            return {"count": None, "status": "bootstrap_pending_other_date"}
        _BOOTSTRAP_JOB.clear()
        _BOOTSTRAP_JOB.update(path=job_path, status="bootstrap_pending")

        def bootstrap() -> None:
            try:
                result = observed_count(trade_date)
            except Exception:
                # Surface a terminal diagnostic; do not repeatedly scan the
                # same broken history or grant orders after a worker failure.
                result = None
            with _BOOTSTRAP_LOCK:
                _BOOTSTRAP_JOB["status"] = (
                    "bootstrap_complete" if result is not None else "bootstrap_failed"
                )

        try:
            threading.Thread(
                target=bootstrap,
                name="entry-recheck-budget-bootstrap",
                daemon=True,
            ).start()
        except RuntimeError:
            _BOOTSTRAP_JOB["status"] = "bootstrap_failed"
            return {"count": None, "status": "bootstrap_failed"}
        return {"count": None, "status": "bootstrap_pending"}
    finally:
        _BOOTSTRAP_LOCK.release()


def _bootstrap_legacy(payload: dict[str, Any], trade_date: str) -> None:
    """Do not reset already-observed same-day recheck orders at first deployment."""
    path = existing_or_gzip_path(
        DATA_DIR / "pipeline_events" / f"pipeline_events_{trade_date}.jsonl"
    )
    if not path.exists():
        return
    with open_text_auto(path, errors="strict") as handle:
        for line in handle:
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("invalid_same_day_bootstrap_event")
            fields = event.get("fields") or {}
            if not isinstance(fields, dict):
                raise ValueError("invalid_same_day_bootstrap_fields")
            if (
                str(fields.get("entry_opportunity_recheck_submit_observed")).lower()
                != "true"
            ):
                continue
            order = str(
                fields.get("entry_opportunity_recheck_broker_order_no") or ""
            ).strip()
            if order in {"", "-"}:
                raise ValueError("legacy_recheck_submit_identity_missing")
            scope = fields.get("entry_opportunity_recheck_scope")
            entry = {
                "status": "accepted",
                "code": str(event.get("stock_code") or "unknown"),
                "scope": scope if scope in SCOPES else "legacy_unknown",
                "broker_order_no": order,
            }
            key = f"legacy:{order}"
            previous = payload["attempts"].get(key)
            if previous is not None and previous != entry:
                raise ValueError("legacy_recheck_order_identity_conflict")
            payload["attempts"][key] = entry


def reserve(
    *,
    trade_date: str,
    attempt_id: str,
    code: str,
    scope: str,
    limit: int,
    per_symbol_limit: int = 1,
) -> dict[str, Any]:
    if (
        not attempt_id
        or not code
        or scope not in SCOPES
        or count(limit) <= 0
        or count(per_symbol_limit) <= 0
    ):
        raise ValueError("invalid_budget_reservation_contract")
    path = _path(trade_date)
    with _locked(path):
        payload = _load(path, trade_date)
        if not path.exists():
            _bootstrap_legacy(payload, trade_date)
            _write(path, payload)
        rows = _charged(payload)
        reason = "reserved"
        if attempt_id in payload["attempts"]:
            reason = "attempt_already_reserved_or_finished"
        elif len(rows) >= limit:
            reason = "daily_buy_recovery_cap_exhausted"
        elif sum(row["code"] == code for row in rows) >= per_symbol_limit:
            reason = "symbol_recheck_submit_cap_exhausted"
        if reason != "reserved":
            return {"allowed": False, "reason": reason, "charged_count": len(rows)}
        payload["attempts"][attempt_id] = {
            "status": "reserved",
            "code": code,
            "scope": scope,
            "broker_order_no": "",
        }
        _write(path, payload)
        return {"allowed": True, "reason": reason, "charged_count": len(rows) + 1}


def definitive_no_order_rejection(response: Any) -> bool:
    """Classify existing transport/owner results, never infer from a timeout."""
    if not isinstance(response, dict):
        return False
    if any(
        str(response.get(key) or "").strip() not in {"", "-"}
        for key in ("ord_no", "odno", "order_no")
    ):
        return False
    codes = [
        str(response[key]).strip()
        for key in ("return_code", "rt_cd")
        if key in response
    ]
    if not codes or "0" in codes or response.get("owner_registry_ambiguous") is True:
        return False
    if response.get("owner_registry_required") is True:
        if response.get("broker_order_attempted") is True:
            return False
        if response.get("broker_order_attempted") is False:
            return True
    # Existing send_buy_order_market returns these before any transport call.
    if all(code in {"PAUSED", "BUY_TIME_BLOCKED"} for code in codes):
        return True
    return all(code.lstrip("-").isdigit() and int(code) != 0 for code in codes)


def settle(
    *,
    trade_date: str,
    attempt_id: str,
    broker_order_no: str = "",
    definitive_reject: bool = False,
) -> None:
    """No time-based release; ambiguous transport outcomes remain reserved."""
    if not broker_order_no and not definitive_reject:
        return
    if broker_order_no and definitive_reject:
        raise ValueError("conflicting_budget_outcome")
    path = _path(trade_date)
    with _locked(path):
        payload = _load(path, trade_date)
        row = payload["attempts"].get(attempt_id)
        if not isinstance(row, dict):
            raise ValueError("budget_reservation_missing")
        target = "accepted" if broker_order_no else "rejected"
        if row["status"] == target and row["broker_order_no"] == broker_order_no:
            return
        if row["status"] != "reserved":
            raise ValueError("budget_outcome_conflict")
        row.update(status=target, broker_order_no=broker_order_no)
        _write(path, payload)
