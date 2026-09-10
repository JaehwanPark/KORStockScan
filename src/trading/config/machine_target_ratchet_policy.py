"""Operator-pinned target amendment scope; no daily reapproval/research gate."""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from src.trading.order.profit_stagnation import _finite
from src.trading.market.target_pressure import CONTRACT

FAMILY = "machine_ws_target_ratchet_v1"
PATH_ENV = "KORSTOCKSCAN_MACHINE_TARGET_RATCHET_POLICY_PATH"
HASH_ENV = "KORSTOCKSCAN_MACHINE_TARGET_RATCHET_POLICY_SHA256"


def load_policy(*, now, owner, entered_at):
    path, pin = os.getenv(PATH_ENV, ""), os.getenv(HASH_ENV, "")
    if not path and not pin:
        return None
    if not path or not pin:
        raise ValueError("ratchet_policy_pin_incomplete")
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin:
        raise ValueError("ratchet_policy_hash_mismatch")
    p = json.loads(raw)
    if (
        not isinstance(p, dict)
        or set(p)
        != {
            "family",
            "enabled",
            "valid_from",
            "valid_until",
            "owners",
            "round_trip_cost_pct",
            "slippage_bps",
            "cost_source_sha256",
            "decision_contract",
        }
        or p["family"] != FAMILY
        or p.get("decision_contract") != CONTRACT
        or type(p["enabled"]) is not bool
    ):
        raise ValueError("ratchet_policy_contract_invalid")
    if (
        not isinstance(p["owners"], list)
        or not p["owners"]
        or any(
            not isinstance(o, str) or o not in {"episode", "widget_auto_trade"}
            for o in p["owners"]
        )
        or len(set(p["owners"])) != len(p["owners"])
    ):
        raise ValueError("ratchet_policy_owner_invalid")
    cost_hash = p["cost_source_sha256"]
    if (
        not isinstance(cost_hash, str)
        or len(cost_hash) != 64
        or any(c not in "0123456789abcdef" for c in cost_hash)
        or not _finite(p["round_trip_cost_pct"])
        or not 0 < p["round_trip_cost_pct"] < 100
        or not _finite(p["slippage_bps"])
        or not 0 <= p["slippage_bps"] < 10000
    ):
        raise ValueError("ratchet_policy_cost_invalid")
    start, end = (datetime.fromisoformat(p[k]) for k in ("valid_from", "valid_until"))
    entered = datetime.fromisoformat(entered_at)
    if any(d.utcoffset() is None for d in (start, end, entered, now)) or start >= end:
        raise ValueError("ratchet_policy_date_invalid")
    if not (p["enabled"] and owner in p["owners"] and start <= entered <= now < end):
        return None
    return p, pin
