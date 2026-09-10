"""Read an operator-pinned exit supplement; never publish or enable a policy.

The existing widget/episode services load this through their owner loops. An
absent pin is OFF. Initial deployment/configuration remains an operator action;
there is no research-floor, daily approval renewal or automatic risk expansion.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from src.trading.order.profit_stagnation import _finite

FAMILY = "machine_profit_stagnation_v1"
PATH_ENV = "KORSTOCKSCAN_MACHINE_PROFIT_STAGNATION_POLICY_PATH"
HASH_ENV = "KORSTOCKSCAN_MACHINE_PROFIT_STAGNATION_POLICY_SHA256"


def validate_policy(policy: dict) -> dict:
    if not isinstance(policy, dict) or policy.get("family") != FAMILY:
        raise ValueError("profit_stagnation_policy_family_invalid")
    required = {
        "family",
        "enabled",
        "valid_from",
        "valid_until",
        "owners",
        "round_trip_cost_pct",
        "slippage_bps",
        "cost_source_sha256",
        "min_sec",
        "max_profit_move",
        "max_peak_improve",
        "sell_ttl_sec",
        "max_observation_gap_sec",
    }
    if set(policy) != required or type(policy["enabled"]) is not bool:
        raise ValueError("profit_stagnation_policy_fields_invalid")
    start, end = (
        datetime.fromisoformat(policy[k]) for k in ("valid_from", "valid_until")
    )
    if start.utcoffset() is None or end.utcoffset() is None or start >= end:
        raise ValueError("profit_stagnation_policy_window_invalid")
    if (
        not isinstance(policy["owners"], list)
        or not policy["owners"]
        or any(type(owner) is not str for owner in policy["owners"])
        or len(set(policy["owners"])) != len(policy["owners"])
        or set(policy["owners"]) - {"widget_auto_trade", "episode"}
    ):
        raise ValueError("profit_stagnation_owner_invalid")
    digest = policy["cost_source_sha256"]
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(c not in "0123456789abcdef" for c in digest)
    ):
        raise ValueError("profit_stagnation_cost_source_missing")
    for key in (
        "round_trip_cost_pct",
        "slippage_bps",
        "max_profit_move",
        "max_peak_improve",
    ):
        if not _finite(policy[key]) or policy[key] < 0:
            raise ValueError("profit_stagnation_numeric_policy_invalid")
    if not 0 < policy["round_trip_cost_pct"] < 100 or policy["slippage_bps"] >= 10000:
        raise ValueError("profit_stagnation_cost_bound_invalid")
    if any(
        type(policy[k]) is not int or policy[k] <= 0
        for k in ("min_sec", "sell_ttl_sec", "max_observation_gap_sec")
    ):
        raise ValueError("profit_stagnation_duration_invalid")
    return policy


def load_policy(
    *, now: datetime, owner: str, entered_at: datetime
) -> tuple[dict, str] | None:
    path, pin = os.getenv(PATH_ENV, ""), os.getenv(HASH_ENV, "")
    if not path and not pin:
        return None
    if not path or not pin:
        raise ValueError("profit_stagnation_policy_pin_incomplete")
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != pin:
        raise ValueError("profit_stagnation_policy_pin_mismatch")
    policy = validate_policy(json.loads(raw))
    start, end = (
        datetime.fromisoformat(policy[k]) for k in ("valid_from", "valid_until")
    )
    if now.utcoffset() is None or entered_at.utcoffset() is None:
        raise ValueError("profit_stagnation_aware_time_required")
    if not (
        policy["enabled"]
        and owner in policy["owners"]
        and start <= entered_at <= now < end
    ):
        return None
    return policy, pin
