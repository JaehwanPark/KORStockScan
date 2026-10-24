"""Explicit append-only reconciliation of a stale terminal snapshot.

This is a journal-storage repair, not a broker receipt producer. It accepts only
an already recorded Main BUY full fill immediately followed by the known stale
terminal transition. No canceled, partial, unbound or retired-owner order can be
recovered by this contract. All original bytes and event hashes remain intact.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json

EVENT = "STALE_TERMINAL_SNAPSHOT_RECONCILED"
CONFIRM = "append-verified-full-fill-terminal-reconciliation"
METADATA = frozenset(
    {"schema", "event_id", "observed_at_kst", "previous_hash", "event_hash"}
)
IDENTITY = (
    "intent_id",
    "account_key",
    "order_date",
    "symbol",
    "side",
    "action",
    "quantity",
    "route",
    "original_order_no",
    "owner_type",
    "owner_id",
    "position_id",
    "client_intent_id",
    "authority_policy_id",
    "authority_policy_hash",
    "broker_order_no",
)


def _exact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def recovery_payload(events, stale, original_prefix):
    """Derive, never supply, the corrected state from two exact source events."""

    def require(ok):
        if not ok:
            raise ValueError("owner_registry_stale_terminal_recovery_proof_invalid")

    require(len(events) >= 2)
    anchor, fill = events[-2:]
    require(
        anchor.get("event") == "ORDER_BOUND" and anchor.get("state") == "ORDER_BOUND"
    )
    require(fill.get("event") == "FILL_RECORDED" and fill.get("state") == "ORDER_BOUND")
    require(
        stale.get("event") == "ORDER_TERMINAL"
        and stale.get("state") == "ORDER_TERMINAL"
    )
    require(stale.get("reason") == "shared_ws_execution_receipt_terminal")
    require(
        all(
            _exact(anchor.get(k)) == _exact(fill.get(k)) == _exact(stale.get(k))
            for k in IDENTITY
        )
    )
    require(
        all(
            anchor.get(k)
            for k in IDENTITY
            if k
            not in {"original_order_no", "authority_policy_id", "authority_policy_hash"}
        )
    )
    require(anchor["side"] == "BUY" and anchor["action"] == "NEW")
    require(anchor["owner_type"] == "main_scalping")
    require(
        anchor["owner_id"] == anchor["position_id"]
        and str(anchor["owner_id"]).startswith("main_scalping:")
    )
    intent_history = [r for r in events if r.get("intent_id") == anchor["intent_id"]]
    require(len(intent_history) == 3 and intent_history[-2:] == [anchor, fill])
    require(intent_history[0].get("event") == "INTENT_RESERVED")
    require(type(anchor["quantity"]) is int and anchor["quantity"] > 0)
    require(
        type(fill.get("filled_qty")) is int and fill["filled_qty"] == anchor["quantity"]
    )
    require(type(fill.get("fill_amount")) is int and fill["fill_amount"] > 0)
    require(str(fill.get("execution_no") or "").isdigit())
    require(
        all(
            type(r.get(k)) is int and r[k] == 0
            for r in (anchor, stale)
            for k in ("filled_qty", "fill_amount")
        )
    )
    require(
        fill.get("previous_hash") == anchor["event_hash"]
        and stale.get("previous_hash") == anchor["event_hash"]
    )
    times = [
        datetime.fromisoformat(r["observed_at_kst"]) for r in (anchor, fill, stale)
    ]
    require(all(t.tzinfo is not None for t in times) and times[0] < times[1] < times[2])
    # Reject additional state/cancellation/amendment fields, even if hash-valid.
    terminal = {k: anchor.get(k) for k in IDENTITY}
    terminal.update(
        event="ORDER_TERMINAL",
        state="ORDER_TERMINAL",
        filled_qty=0,
        fill_amount=0,
        reason="shared_ws_execution_receipt_terminal",
    )
    require(
        _exact({k: v for k, v in stale.items() if k not in METADATA})
        == _exact(terminal)
    )
    fill_expected = {k: anchor.get(k) for k in IDENTITY}
    fill_expected.update(
        event="FILL_RECORDED",
        state="ORDER_BOUND",
        filled_qty=fill["filled_qty"],
        fill_amount=fill["fill_amount"],
        execution_no=fill["execution_no"],
    )
    require(
        _exact({k: v for k, v in fill.items() if k not in METADATA})
        == _exact(fill_expected)
    )
    require(original_prefix.endswith(b"\n"))
    return {
        **terminal,
        "event": EVENT,
        "filled_qty": fill["filled_qty"],
        "fill_amount": fill["fill_amount"],
        "reason": "verified_existing_full_fill_before_stale_terminal",
        "recovery_source": {
            "schema": "owner_journal_stale_terminal_recovery_v1",
            "anchor_event_hash": anchor["event_hash"],
            "fill_event_hash": fill["event_hash"],
            "stale_terminal_event_hash": stale["event_hash"],
            "journal_prefix_sha256": hashlib.sha256(original_prefix).hexdigest(),
            "journal_prefix_bytes": len(original_prefix),
            "journal_prefix_lines": len(original_prefix.splitlines()),
        },
    }


def validate_recovery(events, stale, receipt, original_prefix):
    expected = recovery_payload(events, stale, original_prefix)
    actual = {k: v for k, v in receipt.items() if k not in METADATA}
    if (
        _exact(actual) != _exact(expected)
        or receipt.get("previous_hash") != stale["event_hash"]
    ):
        raise ValueError("owner_registry_stale_terminal_recovery_receipt_invalid")
    if datetime.fromisoformat(receipt["observed_at_kst"]) <= datetime.fromisoformat(
        stale["observed_at_kst"]
    ):
        raise ValueError("owner_registry_stale_terminal_recovery_time_invalid")


def main(argv=None):
    import argparse
    from pathlib import Path
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    if args.confirm and args.confirm != CONFIRM:
        parser.error("invalid confirmation")
    result = OrderOwnerRegistry(args.journal).reconcile_stale_terminal_tail(
        expected_sha256=args.expected_sha256, apply=args.confirm == CONFIRM
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
