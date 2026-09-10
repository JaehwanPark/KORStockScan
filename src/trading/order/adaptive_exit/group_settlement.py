"""Exact closed position census before a pooled residual SELL or archival.

Quantities only. Every cancellation needs its own positive confirmation; an
ACK, net balance, BOOK allocation or missing cost is never a fill/PnL receipt.
"""

from copy import deepcopy

from .group_terminal import IDENTITY, _terminal_order
from .target_group import _digest


def closed_census(rows, *, pending_buy_ids=()):
    if not rows or len({r["intent_id"] for r in rows}) != len(rows):
        raise ValueError("whole_exit_census_empty_or_duplicate")
    scope = (
        "account_key",
        "owner_type",
        "owner_id",
        "position_id",
        "symbol",
        "order_date",
    )
    if any(any(r.get(k) != rows[0].get(k) for k in scope) for r in rows):
        raise ValueError("whole_exit_census_scope_conflict")
    if len(set(pending_buy_ids)) != len(pending_buy_ids) or not set(
        pending_buy_ids
    ) <= {
        r["intent_id"]
        for r in rows
        if r.get("side") == "BUY" and r.get("action") == "NEW"
    }:
        raise ValueError("whole_exit_pending_buy_census_missing")
    buys, sells, cancels = [], [], []
    for row in rows:
        if row.get("state") != "ORDER_TERMINAL":
            raise ValueError("whole_exit_census_not_terminal")
        if row.get("side") == "BUY" and row.get("action") == "NEW":
            if (
                type(row.get("quantity")) is not int
                or row["quantity"] <= 0
                or type(row.get("filled_qty")) is not int
                or not 0 <= row["filled_qty"] <= row["quantity"]
                or (
                    row["intent_id"] not in pending_buy_ids
                    and row["filled_qty"] != row["quantity"]
                )
            ):
                raise ValueError("whole_exit_full_buy_required")
            buy = {k: row[k] for k in IDENTITY}
            if row["intent_id"] in pending_buy_ids:
                proof = row.get("terminal_reconciliation")
                if (
                    not isinstance(proof, dict)
                    or proof.get("schema") != "order_owner_terminal_reconciliation_v1"
                    or proof.get("source_contract")
                    != "machine_adaptive_exit_buy_dated_current_v1"
                    or type(proof.get("quantity")) is not int
                    or type(proof.get("filled_qty")) is not int
                    or any(proof.get(k) != row.get(k) for k in IDENTITY)
                    or not _digest(proof.get("receipt_sha256"))
                ):
                    raise ValueError("whole_exit_exact_pending_buy_proof_required")
                buy["reconciliation_sha256"] = proof["receipt_sha256"]
            buys.append(buy)
        elif row.get("side") == "SELL" and row.get("action") == "NEW":
            sells.append(_terminal_order(row, "adaptive_whole_exit"))
        elif row.get("side") in {"BUY", "SELL"} and row.get("action") == "CANCEL":
            cancels.append(row)
        else:
            raise ValueError("whole_exit_census_unrecognized_action")
    if not buys or not sells:
        raise ValueError("whole_exit_census_roots_missing")
    roots = {
        r["broker_order_no"]: r
        for r in rows
        if (r.get("side") == "SELL" or r["intent_id"] in pending_buy_ids)
        and r.get("action") == "NEW"
    }
    canceled, proofs = {k: 0 for k in roots}, []
    for child in cancels:
        root = roots.get(child.get("original_order_no"))
        partial = child.get("cancel_reconciliation")
        terminal = child.get("terminal_cancel_reconciliation")
        proof = partial if partial is not None else terminal
        if (
            root is None
            or child.get("side") != root.get("side")
            or (partial is not None and terminal is not None)
            or type(child.get("filled_qty")) is not int
            or child["filled_qty"] != 0
            or type(child.get("quantity")) is not int
            or child["quantity"] <= 0
            or child.get("route") != root.get("route")
            or not isinstance(proof, dict)
            or type(proof.get("confirmed_qty")) is not int
            or not 0 < proof["confirmed_qty"] <= child["quantity"]
            or not _digest(proof.get("receipt_sha256"))
            or any(
                proof.get(k) != v
                for k, v in {
                    "target_intent_id": root["intent_id"],
                    "cancel_intent_id": child["intent_id"],
                    "target_order_no": root["broker_order_no"],
                    "cancel_order_no": child["broker_order_no"],
                    "order_date": root["order_date"],
                }.items()
            )
        ):
            raise ValueError("whole_exit_cancel_identity_or_confirmation_missing")
        if partial is not None:
            if (
                root.get("side") != "SELL"
                or root.get("partial_cancel_reconciliation") != proof
                or proof.get("schema") != "order_owner_partial_cancel_reconciliation_v1"
                or proof.get("source_contract")
                != "machine_adaptive_exit_full_cancel_request_dated_current_v1"
                or proof["confirmed_qty"] != child["quantity"]
            ):
                raise ValueError("whole_exit_partial_cancel_proof_conflict")
        elif (
            root.get("terminal_cancel_reconciliation") != proof
            or proof.get("schema") != "order_owner_terminal_cancel_reconciliation_v1"
            or proof.get("source_contract")
            != (
                "machine_adaptive_exit_buy_terminal_cancel_dated_current_v1"
                if root["side"] == "BUY"
                else "machine_adaptive_exit_terminal_cancel_dated_current_v1"
            )
            or type(proof.get("requested_qty")) is not int
            or proof["requested_qty"] != child["quantity"]
            or type(proof.get("filled_qty")) is not int
            or proof["filled_qty"] != root["filled_qty"]
            or type(proof.get("remaining_qty")) is not int
            or proof["remaining_qty"] != 0
        ):
            raise ValueError("whole_exit_terminal_cancel_proof_conflict")
        canceled[root["broker_order_no"]] += proof["confirmed_qty"]
        proofs.append(deepcopy(proof))
    for number, root in roots.items():
        if (
            type(root.get("canceled_qty", 0)) is not int
            or root.get("canceled_qty", 0) != canceled[number]
            or root["quantity"] != root["filled_qty"] + canceled[number]
        ):
            raise ValueError("whole_exit_cancel_quantity_conservation_failed")
    bought, sold = sum(r["filled_qty"] for r in buys), sum(
        r["filled_qty"] for r in sells
    )
    if sold > bought:
        raise ValueError("whole_exit_census_oversold")
    return {
        "buy_orders": buys,
        "orders": sells,
        "cancel_proofs": proofs,
        "buy_filled_qty": bought,
        "sell_filled_qty": sold,
        "residual_qty": bought - sold,
    }
