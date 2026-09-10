"""Execution-only terminal ledger under the original order owner.

Registry fills and dated reconciliation prove quantities, not exact notional or
commission allocation. Keep economics null until a separately verified exact
settlement source arrives. This ledger never submits orders or approves policy.
"""

from copy import deepcopy
from dataclasses import asdict, replace

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256

SCHEMA = "machine_adaptive_exit_execution_terminal_v1"
TERMINAL_KEY = "adaptive_exit_execution_terminal"


def owner_cancel_client_id(binding_hash, order):
    return canonical_sha256(
        {"binding": binding_hash, "order": asdict(order), "action": "cancel"}
    )


def confirmed_cancel_proof(*, session, adapter, order):
    """Require a cancel's own terminal proof; a root fill never closes an ACK."""
    child = adapter.registry.intent_for_client(
        context=replace(
            session.context,
            client_intent_id=owner_cancel_client_id(session.binding_hash, order),
        )
    )
    if child is None:
        return None
    root = adapter._owned(order)
    proof = child.get("terminal_cancel_reconciliation")
    if (
        root.get("state") != "ORDER_TERMINAL"
        or child.get("state") != "ORDER_TERMINAL"
        or child.get("action") != "CANCEL"
        or child.get("side") != "SELL"
        or child.get("original_order_no") != order.order_no
        or child.get("authority_policy_hash") != session.policy.policy_hash
        or child.get("authority_policy_id") != "machine_adaptive_exit_v1"
        or any(
            child.get(k) != root.get(k)
            for k in (
                "symbol",
                "route",
                "order_date",
                "owner_type",
                "owner_id",
                "position_id",
                "account_key",
            )
        )
        or not isinstance(proof, dict)
        or any(
            type(row.get(k)) is not int
            for row, k in (
                (root, "quantity"),
                (root, "filled_qty"),
                (root, "canceled_qty"),
                (child, "quantity"),
                (proof, "requested_qty"),
                (proof, "filled_qty"),
                (proof, "remaining_qty"),
            )
        )
        or root.get("terminal_cancel_reconciliation") != proof
        or any(
            proof.get(k) != v
            for k, v in {
                "schema": "order_owner_terminal_cancel_reconciliation_v1",
                "source_contract": "machine_adaptive_exit_terminal_cancel_dated_current_v1",
                "target_intent_id": root["intent_id"],
                "cancel_intent_id": child["intent_id"],
                "target_order_no": order.order_no,
                "cancel_order_no": child.get("broker_order_no"),
                "order_date": order.trading_date,
                "requested_qty": child["quantity"],
                "filled_qty": root["filled_qty"],
                "remaining_qty": 0,
            }.items()
        )
        or type(proof.get("confirmed_qty")) is not int
        or not 0 < proof["confirmed_qty"] <= child["quantity"]
        or root.get("canceled_qty") != proof["confirmed_qty"]
        or root["quantity"] != root["filled_qty"] + proof["confirmed_qty"]
        or not isinstance(proof.get("receipt_sha256"), str)
        or len(proof["receipt_sha256"]) != 64
        or any(c not in "0123456789abcdef" for c in proof["receipt_sha256"])
    ):
        raise ValueError("adaptive_terminal_cancel_child_proof_required")
    return deepcopy(proof)


def terminal_receipt(*, session, adapter, observed_at_ms):
    session.validate()
    if (
        adapter.context != session.context
        or adapter.policy_hash != session.policy.policy_hash
        or adapter.symbol != session.policy.scope_key.split("|")[2]
    ):
        raise ValueError("adaptive_terminal_adapter_binding_invalid")
    s = session.driver.orders
    if s.phase != "FLAT" or s.open_qty or s.reserved_qty:
        raise ValueError("adaptive_terminal_requires_flat_lot")
    if (
        type(observed_at_ms) is not int
        or observed_at_ms < session.position.first_fill_at_ms
    ):
        raise ValueError("adaptive_terminal_observation_time_invalid")
    rows, cancels = [], []
    predecessor = s.target
    for index, key in enumerate((s.target, *s.exit_order_history)):
        row = adapter._owned(key)
        filled = row.get("filled_qty")
        reconciliation = row.get("terminal_reconciliation")
        if not isinstance(reconciliation, dict):
            raise ValueError("adaptive_terminal_exact_registry_proof_missing")
        proof = reconciliation.get("receipt_sha256")
        if (
            row.get("state") != "ORDER_TERMINAL"
            or type(filled) is not int
            or not 0 <= filled <= row["quantity"]
            or reconciliation.get("schema") != "order_owner_terminal_reconciliation_v1"
            or reconciliation.get("source_contract")
            != "machine_adaptive_exit_dated_current_v1"
            or any(
                reconciliation.get(k) != row.get(k)
                for k in (
                    "account_key",
                    "intent_id",
                    "order_date",
                    "broker_order_no",
                    "owner_type",
                    "owner_id",
                    "position_id",
                    "client_intent_id",
                    "symbol",
                    "side",
                    "action",
                    "route",
                    "quantity",
                    "filled_qty",
                )
            )
            or not isinstance(proof, str)
            or len(proof) != 64
            or any(c not in "0123456789abcdef" for c in proof)
        ):
            raise ValueError("adaptive_terminal_exact_registry_proof_missing")
        if index == 0:
            if (
                row["intent_id"] != session.target_intent_id
                or filled != s.target_filled_qty
            ):
                raise ValueError("adaptive_terminal_target_mismatch")
        elif (
            row.get("client_intent_id") != adapter._replacement_client_id(predecessor)
            or row.get("authority_policy_id") != "machine_adaptive_exit_v1"
            or row.get("authority_policy_hash") != session.policy.policy_hash
        ):
            raise ValueError("adaptive_terminal_replacement_chain_mismatch")
        child_proof = confirmed_cancel_proof(
            session=session, adapter=adapter, order=key
        )
        child_id = child_proof["cancel_intent_id"] if child_proof else None
        census = adapter.registry.position_intents(
            context=session.context, symbol=adapter.symbol
        )
        if any(
            r.get("order_date") == key.trading_date
            and r.get("original_order_no") == key.order_no
            and r["intent_id"] != child_id
            for r in census
        ):
            raise ValueError("adaptive_terminal_unresolved_cancel_or_successor")
        if child_proof is not None:
            cancels.append(child_proof)
        rows.append(
            {
                **asdict(key),
                "intent_id": row["intent_id"],
                "client_intent_id": row["client_intent_id"],
                "role": "original_target" if index == 0 else "adaptive_replacement",
                "route": row["route"],
                "requested_qty": row["quantity"],
                "filled_qty": filled,
                "remaining_qty": 0,
                "unfilled_terminal_qty": row["quantity"] - filled,
                "reconciliation_sha256": proof,
                "fill_amount_krw": None,
                "commission_krw": None,
                "tax_krw": None,
            }
        )
        predecessor = key
    if (
        sum(row["filled_qty"] for row in rows[1:]) != s.exit_filled_qty
        or sum(row["filled_qty"] for row in rows) != s.buy_filled_qty
    ):
        raise ValueError("adaptive_terminal_fill_conservation_mismatch")
    payload = {
        "schema": SCHEMA,
        "terminal_id": session.binding_hash,
        "session_sha256": session.to_payload()["canonical_sha256"],
        "scope_key": session.policy.scope_key,
        "owner_type": session.context.owner_type,
        "owner_id": session.context.owner_id,
        "position_id": session.context.position_id,
        "lot_id": session.position.lot_id,
        "observed_at_ms": observed_at_ms,
        "execution_status": "reconciled_flat",
        "buy_filled_qty": s.buy_filled_qty,
        "sell_filled_qty": sum(row["filled_qty"] for row in rows),
        "orders": rows,
        "cancel_proofs": cancels,
        "realized_pnl_status": "unreconciled_exact_fill_cost_required",
        "realized_net_profit_krw": None,
        "economic_acceptance": False,
        "new_entry_authority": False,
    }
    return {**payload, "canonical_sha256": canonical_sha256(payload)}


def validate_terminal(receipt, session):
    """Integrity check of an owner-produced receipt; not independent authority."""
    if not isinstance(receipt, dict):
        raise ValueError("adaptive_terminal_receipt_missing")
    if (
        receipt.get("schema") != SCHEMA
        or receipt.get("canonical_sha256")
        != canonical_sha256(
            {k: v for k, v in receipt.items() if k != "canonical_sha256"}
        )
        or receipt.get("terminal_id") != session.binding_hash
        or receipt.get("session_sha256") != session.to_payload()["canonical_sha256"]
        or session.manager_required
        or receipt.get("execution_status") != "reconciled_flat"
    ):
        raise ValueError("adaptive_terminal_receipt_binding_invalid")


def same_terminal(existing, candidate):
    """A repeated observation cannot silently replace fill/accounting evidence."""
    ignored = {"canonical_sha256", "observed_at_ms"}
    if {k: v for k, v in existing.items() if k not in ignored} != {
        k: v for k, v in candidate.items() if k not in ignored
    }:
        raise ValueError("adaptive_terminal_receipt_conflict")
