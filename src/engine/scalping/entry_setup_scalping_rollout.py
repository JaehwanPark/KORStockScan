"""Pinned operator rollout of the existing V2.14 entry owner to all SCALPING.

This is a prompt-scope approval, not an economic promotion or a new order owner.
The durable accepted-order ledger, one-share and all execution guards remain.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
PATH_ENV = "KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_PATH"
SHA_ENV = "KORSTOCKSCAN_SCALPING_V2_14_ROLLOUT_SHA256"
SCHEMA = "operator_scalping_v2_14_rollout_v1"
SCOPES = (
    "KRX|KRX_REGULAR",
    "NXT|KRX_REGULAR",
    "NXT|NXT_REGULAR_OVERLAP",
    "NXT|NXT_REGULAR",
    "PREMARKET_KRX_LIKE|PREMARKET_KRX_LIKE",
    "NXT|NXT_PREMARKET",
    "PREMARKET_KRX_LIKE|NXT_PREMARKET",
    "NXT|NXT_AFTERMARKET",
)
CONTRACT = {
    "schema": SCHEMA,
    "strategy": "SCALPING",
    "stage": "entry",
    "position_tags": "all",
    "scopes": list(SCOPES),
    "one_share_probe_first_required": True,
    "residual_multi_leg_forbidden": True,
    "scale_in_forbidden": True,
    "maximum_daily_exploration_probes": 100,
    "cap_basis": "existing_global_durable_broker_accepted_probe_orders",
    "preserve_execution_guards": True,
    "persistence": "until_operator_revocation",
}


def load_rollout(
    *, now: datetime | None = None, env: dict[str, str] | None = None
) -> dict[str, Any] | None:
    source = os.environ if env is None else env
    path, digest = source.get(PATH_ENV, ""), source.get(SHA_ENV, "")
    if not path and not digest:
        return None
    result: dict[str, Any] = {"valid": False, "reason": "rollout_pin_invalid"}
    try:
        if not Path(path).is_absolute():
            return result
        raw = Path(path).read_bytes()
        if len(digest) != 64 or hashlib.sha256(raw).hexdigest() != digest:
            return result
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return result
        current = (now or datetime.now(KST)).astimezone(KST)
        effective = datetime.fromisoformat(payload["effective_from"])
        if effective.tzinfo is None or effective > current:
            return {**result, "reason": "rollout_not_effective"}
        if any(
            type(payload.get(k)) is not type(v) or payload.get(k) != v
            for k, v in CONTRACT.items()
        ):
            return {**result, "reason": "rollout_contract_invalid"}
        if (
            re.fullmatch(r"[0-9a-f]{40}", str(payload.get("reviewed_commit") or ""))
            is None
        ):
            return result
        if payload.get("operator_authority") != "all_scalping_v2_14_2026_09_11":
            return result
        return {"valid": True, "sha256": digest, "path": path, "payload": payload}
    except (OSError, ValueError, TypeError, KeyError):
        return result


def scope_authorized(
    strategy: Any, venue: Any, session: Any, *, now: datetime | None = None
) -> bool:
    if str(strategy or "").strip().upper() not in {"SCALPING", "SCALP"}:
        return False
    scope = f"{str(venue or '').strip().upper()}|{str(session or '').strip().upper()}"
    rollout = load_rollout(now=now)
    return bool(scope in SCOPES and rollout and rollout.get("valid") is True)


def authorized_scopes(
    *, env: dict[str, str] | None = None, now: datetime | None = None
) -> frozenset[str]:
    rollout = load_rollout(env=env, now=now)
    from src.engine.scalping.entry_recheck_policy import runtime_scope

    return (
        frozenset(runtime_scope(*scope.split("|")) for scope in SCOPES)
        if rollout and rollout.get("valid") is True
        else frozenset()
    )


def decision_authorized(
    strategy: Any, decision: Any, *, now: datetime | None = None
) -> bool:
    current = (now or datetime.now(KST)).astimezone(KST)
    if not isinstance(decision, dict):
        return False
    rollout = load_rollout(now=current)
    return bool(
        rollout
        and rollout.get("valid") is True
        and decision.get("entry_setup_live_policy_scope_authority")
        == "operator_all_scalping_rollout"
        and decision.get("entry_setup_live_policy_runtime_effect") is True
        and decision.get("entry_setup_live_policy_target_date")
        == current.date().isoformat()
        and decision.get("entry_setup_live_policy_activation_sha256")
        == rollout["sha256"]
        and scope_authorized(
            strategy,
            decision.get("entry_setup_live_policy_effective_venue"),
            decision.get("entry_setup_live_policy_session_bucket"),
            now=current,
        )
    )


def main(argv: list[str] | None = None) -> int:
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(
        description="Publish the explicitly approved persistent SCALPING V2.14 scope."
    )
    parser.add_argument("--effective-from", required=True)
    parser.add_argument("--reviewed-commit", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--confirm", required=True, choices=["APPLY_ALL_SCALPING_V2_14"]
    )
    args = parser.parse_args(argv)
    effective = datetime.fromisoformat(args.effective_from)
    if (
        effective.tzinfo is None
        or re.fullmatch(r"[0-9a-f]{40}", args.reviewed_commit) is None
    ):
        parser.error("aware effective timestamp and full reviewed commit required")
    output = Path(args.output)
    if output.exists():
        parser.error(
            "use a new immutable approval path; existing approvals cannot be overwritten"
        )
    payload = {
        **CONTRACT,
        "operator_authority": "all_scalping_v2_14_2026_09_11",
        "effective_from": effective.astimezone(KST).isoformat(),
        "reviewed_commit": args.reviewed_commit,
        "generated_at": datetime.now(KST).isoformat(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".rollout-", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        # Atomic publish without replacing an existing approval, including races.
        os.link(temporary, output)
    finally:
        Path(temporary).unlink(missing_ok=True)
    print(
        json.dumps(
            {
                "path": str(output.resolve()),
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
