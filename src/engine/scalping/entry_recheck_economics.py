"""Receipt-only economics for an existing recheck-owned position cycle.

Consumes already-reconciled local receipts; no Kiwoom parsing or order authority.
The ledger survives transient entry/add bundle cleanup through attribution keys.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.engine.scalping.entry_recheck_policy import count, finite_number

LEDGER_KEY = "entry_opportunity_recheck_buy_receipts"
SCHEMA = "entry_recheck_position_economics_v1"
PREFIX = "entry_opportunity_recheck_"


def record_buy_receipt(
    stock: dict[str, Any], receipt: Mapping[str, Any], *, kind: str
) -> None:
    """Accumulate cumulative order receipts idempotently, never raw fill deltas."""
    attempt = str(stock.get(PREFIX + "attempt_id") or "")
    if not attempt:
        return
    prior = stock.get(LEDGER_KEY)
    ledger = (
        dict(prior)
        if isinstance(prior, dict)
        else {
            "schema": SCHEMA,
            "attempt_id": attempt,
            "orders": {},
            "invalid": False,
        }
    )
    if prior is not None and not isinstance(prior, dict):
        ledger["invalid"] = True
    if ledger.get("schema") != SCHEMA or ledger.get("attempt_id") != attempt:
        ledger["invalid"] = True
    order = str(receipt.get("order_no") or "").strip()
    qty = count(receipt.get("cumulative_qty"))
    requested = count(receipt.get("requested_qty"))
    amount = finite_number(receipt.get("cumulative_amount"))
    rows = ledger.get("orders")
    if not isinstance(rows, dict):
        rows = {}
        ledger["invalid"] = True
    rows = {
        key: dict(value) if isinstance(value, dict) else value
        for key, value in rows.items()
    }
    previous = rows.get(order)
    row = {
        "qty": qty,
        "requested_qty": requested,
        "amount_krw": amount,
        "kind": kind,
        "bundle_id": str(stock.get("entry_split_probe_bundle_id") or ""),
        "economics_complete": (
            receipt.get("economics_complete") is True
            and receipt.get("quantity_contract_complete") is True
            and receipt.get("unit_fill_consistent") is True
        ),
    }
    if (
        order in {"", "-"}
        or kind not in {"entry", "add"}
        or qty <= 0
        or requested < qty
        or amount is None
        or amount <= 0
    ):
        ledger["invalid"] = True
    elif previous is not None and (
        not isinstance(previous, dict)
        or previous.get("kind") != kind
        or previous.get("bundle_id") != row["bundle_id"]
        or previous.get("requested_qty") != requested
        or count(previous.get("qty")) > qty
        or (finite_number(previous.get("amount_krw")) or 0) > amount
        or (previous.get("qty") == qty and previous != row)
    ):
        ledger["invalid"] = True
    else:
        rows[order] = row
    ledger["orders"] = rows
    stock[LEDGER_KEY] = ledger


def recovered_fill_fields(stock: Mapping[str, Any]) -> dict[str, Any]:
    """Join a receipt arriving before REST acceptance by the exact order ID.

    Never infer a fill from acceptance, quote, holdings or an unrelated order.
    Receipt time is not replaced with the later REST response time.
    """
    if not stock.get(PREFIX + "direct_submit") or not stock.get(
        PREFIX + "submit_observed"
    ):
        return {}
    ledger = stock.get(LEDGER_KEY)
    if not isinstance(ledger, Mapping) or ledger.get("invalid") is not False:
        return {}
    if ledger.get("schema") != SCHEMA or ledger.get("attempt_id") != stock.get(
        PREFIX + "attempt_id"
    ):
        return {}
    orders = ledger.get("orders")
    order = stock.get(PREFIX + "broker_order_no")
    row = orders.get(order) if isinstance(orders, Mapping) else None
    if not isinstance(row, Mapping):
        return {}
    amount = finite_number(row.get("amount_krw"))
    if (
        row.get("kind") != "entry"
        or count(row.get("qty")) != 1
        or count(row.get("requested_qty")) != 1
        or row.get("economics_complete") is not True
        or amount is None
        or amount <= 0
    ):
        return {}
    return {
        PREFIX + "fill_observed": True,
        PREFIX + "fill_order_no": order,
        PREFIX + "fill_price": amount,
        PREFIX + "fill_qty": 1,
    }


def terminal_economics(
    stock: Mapping[str, Any], fields: Mapping[str, Any]
) -> dict[str, Any]:
    """Reconcile the full closed position, keeping mixed-owner PnL diagnostic."""
    result = {
        PREFIX + "economics_schema": SCHEMA,
        PREFIX + "economics_complete": False,
        PREFIX + "economics_decision_eligible": False,
        PREFIX + "economics_cohort": "unreconciled",
        PREFIX + "economics_reason": "buy_sell_receipt_contract_incomplete",
        PREFIX + "economics_source": "broker_position_receipts_fee_aware",
        PREFIX + "cost_adjusted_profit_pct": None,
        PREFIX + "realized_net_pnl_krw": None,
    }
    ledger = stock.get(LEDGER_KEY)
    if not isinstance(ledger, Mapping) or ledger.get("invalid") is not False:
        return result
    if ledger.get("schema") != SCHEMA or ledger.get("attempt_id") != stock.get(
        PREFIX + "attempt_id"
    ):
        return result
    orders = ledger.get("orders")
    if not isinstance(orders, Mapping) or not orders:
        return result
    probe_order = str(stock.get(PREFIX + "broker_order_no") or "")
    probe = orders.get(probe_order)
    if (
        not isinstance(probe, Mapping)
        or probe.get("qty") != 1
        or probe.get("requested_qty") != 1
        or probe.get("kind") != "entry"
    ):
        return result
    buy_qty, buy_amount = 0, 0.0
    mixed, partial = False, False
    bundle = str(probe.get("bundle_id") or "")
    for order, row in orders.items():
        if (
            not isinstance(row, Mapping)
            or not str(order).strip()
            or row.get("economics_complete") is not True
        ):
            return result
        qty, requested = count(row.get("qty")), count(row.get("requested_qty"))
        amount = finite_number(row.get("amount_krw"))
        if qty <= 0 or requested < qty or amount is None or amount <= 0:
            return result
        if row.get("kind") not in {"entry", "add"}:
            return result
        mixed |= row.get("kind") == "add"
        if (
            order != probe_order
            and row.get("kind") == "entry"
            and (not bundle or row.get("bundle_id") != bundle)
        ):
            return result
        buy_qty += qty
        buy_amount += amount
        partial |= qty < requested
    sell_qty = count(fields.get("cumulative_sell_qty"))
    sell_amount = finite_number(fields.get(PREFIX + "sell_notional_krw"))
    cost_rate = finite_number(fields.get(PREFIX + "cost_rate"))
    if (
        fields.get("sell_execution_receipt_economics_complete") is not True
        or fields.get("sell_execution_receipt_quantity_contract_complete") is not True
        or fields.get("sell_execution_receipt_unit_fill_consistent") is not True
        or sell_qty != buy_qty
        or sell_qty <= 0
        or sell_amount is None
        or sell_amount <= 0
        or cost_rate is None
        or not 0 <= cost_rate < 1
    ):
        return result
    exploration = bool(stock.get(PREFIX + "exploration_probe_only"))
    if exploration and (buy_qty != 1 or mixed):
        return result
    cohort = (
        "scale_in_mixed"
        if mixed
        else (
            "probe_only"
            if buy_qty == 1
            else (
                "probe_residual_partial_fill" if partial else "probe_residual_full_fill"
            )
        )
    )
    net = round(sell_amount * (1 - cost_rate) - buy_amount)
    result.update(
        {
            PREFIX + "economics_complete": True,
            PREFIX + "economics_decision_eligible": not mixed,
            PREFIX + "economics_cohort": cohort,
            PREFIX
            + "economics_reason": (
                "mixed_owner_diagnostic_only"
                if mixed
                else "position_receipts_reconciled"
            ),
            PREFIX + "cost_adjusted_profit_pct": net / buy_amount * 100,
            PREFIX + "realized_net_pnl_krw": net,
            PREFIX + "buy_notional_krw": buy_amount,
            PREFIX + "sell_notional_krw": sell_amount,
            PREFIX + "cost_rate": cost_rate,
            PREFIX + "position_qty": buy_qty,
            PREFIX + "buy_order_count": len(orders),
        }
    )
    return result
