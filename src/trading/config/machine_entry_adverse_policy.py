"""Explicit first-deployment pin; automatic consumption, no daily EV gate."""

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path

from src.trading.market.entry_adverse_flow import CONTRACT

PATH_ENV = "KORSTOCKSCAN_MACHINE_ENTRY_ADVERSE_POLICY_PATH"
HASH_ENV = "KORSTOCKSCAN_MACHINE_ENTRY_ADVERSE_POLICY_SHA256"
SCOPE_FIELDS = ("owner", "scope_id", "symbol", "route", "session")


def load_policy(*, scope, now, signal_at):
    path, pin = os.getenv(PATH_ENV, ""), os.getenv(HASH_ENV, "")
    if not path and not pin:
        return None
    if not path or len(pin) != 64:
        raise ValueError("entry_adverse_pin_incomplete")
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin:
        raise ValueError("entry_adverse_pin_mismatch")
    p = json.loads(raw)
    if (
        not isinstance(p, dict)
        or set(p)
        != {
            "contract",
            "enabled",
            "valid_from",
            "valid_until",
            "scopes",
            "approval_reference",
        }
        or p["contract"] != CONTRACT
        or type(p["enabled"]) is not bool
    ):
        raise ValueError("entry_adverse_policy_invalid")
    if (
        not isinstance(p["approval_reference"], str)
        or not p["approval_reference"].strip()
    ):
        raise ValueError("entry_adverse_approval_missing")
    scopes = p["scopes"]
    all_existing = scopes == "all_existing_widget_episode"
    if not all_existing and (not isinstance(scopes, list) or not scopes):
        raise ValueError("entry_adverse_scopes_required")
    rows = [scope] if all_existing else scopes
    for row in rows:
        if (
            not isinstance(row, dict)
            or set(row) != set(SCOPE_FIELDS)
            or any(
                not isinstance(row[k], str) or not row[k] or "*" in row[k]
                for k in SCOPE_FIELDS
            )
            or row["owner"] not in {"widget", "episode"}
            or row["route"] not in {"KRX", "SOR", "NXT"}
            or not re.fullmatch(r"[0-9]{6}", row["symbol"])
        ):
            raise ValueError("entry_adverse_scope_invalid")
    if not all_existing and len(
        {tuple(row[k] for k in SCOPE_FIELDS) for row in rows}
    ) != len(rows):
        raise ValueError("entry_adverse_duplicate_scope")
    start = datetime.fromisoformat(p["valid_from"])
    end = (
        datetime.fromisoformat(p["valid_until"])
        if p["valid_until"] is not None
        else None
    )
    if any(t.utcoffset() is None for t in (start, now, signal_at)) or (
        end is not None and (end.utcoffset() is None or end <= start)
    ):
        raise ValueError("entry_adverse_time_invalid")
    if (
        not p["enabled"]
        or (not all_existing and scope not in scopes)
        or not start <= signal_at <= now
        or (end is not None and now >= end)
    ):
        return None
    return dict(policy=p, pin=pin)
