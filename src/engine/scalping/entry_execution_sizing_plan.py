"""Atomic, behavior-equivalent execution sizing receipt for scalping entries.

The existing position-sizing allocator still owns total quantity and the
existing entry split/price resolvers still own leg shape and numeric prices.
This module only validates and binds those already-authorized results into one
immutable plan.  It cannot authorize an entry or increase quantity.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA_VERSION = "entry_execution_sizing_plan_v1"
PRICE_SCHEMA_VERSION = "entry_price_plan_v1"
POLICY_VERSION = "execution_sizing_baseline_v1"
OWNER = "entry_execution_sizing_owner"
PRICE_OWNER = "existing_entry_price_and_split_resolvers"
QUANTITY_OWNER = "position_sizing_dynamic_formula"


def _positive_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def _content_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _price_candidate_id(order: dict[str, Any], index: int) -> str:
    existing = str(order.get("price_candidate_id") or "").strip()
    if existing:
        return existing
    mode = str(
        order.get("entry_split_order_execution_mode")
        or order.get("price_source")
        or "current_resolver"
    ).strip()
    return f"{mode}:leg{index}"


def compose_entry_execution_sizing_plan(
    planned_orders: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None,
    *,
    expected_total_qty: int,
    action_receipt: dict[str, Any] | None,
    quantity_policy_version: str | None,
    split_policy_version: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Validate and decorate an existing entry plan without changing it.

    Probe-first plans contain only the immediately submitted one-share order;
    their frozen continuation owns the residual quantities.  Both parts are
    included in the same conservation check and plan hash.
    """

    orders = [dict(item) for item in (planned_orders or []) if isinstance(item, dict)]
    receipt = action_receipt if isinstance(action_receipt, dict) else {}
    expected_total_qty = _positive_int(expected_total_qty)
    action_receipt_id = str(receipt.get("evaluation_attempt_id") or "").strip()
    action_owner = str(receipt.get("entry_primary_decision_owner") or "").strip()
    machine_action = str(receipt.get("entry_mechanistic_action") or "").strip().upper()
    ai_screen_pass = receipt.get("entry_ai_screen_pass") is True

    blockers: list[str] = []
    if not action_receipt_id:
        blockers.append("action_receipt_id_missing")
    if action_owner != "mechanistic_entry_adjudicator":
        blockers.append("entry_action_owner_invalid")
    if machine_action != "ENTER_NOW":
        blockers.append("entry_action_not_enter_now")
    if not ai_screen_pass:
        blockers.append("auxiliary_ai_pass_missing")
    if expected_total_qty <= 0:
        blockers.append("expected_total_qty_invalid")
    if not orders:
        blockers.append("planned_orders_missing")

    immediate_qty = sum(_positive_int(item.get("qty")) for item in orders)
    continuation: dict[str, Any] | None = None
    if len(orders) == 1 and isinstance(
        orders[0].get("entry_split_order_probe_continuation"), dict
    ):
        continuation = dict(orders[0]["entry_split_order_probe_continuation"])
    residual_quantities = (
        [
            _positive_int(value)
            for value in continuation.get("residual_quantities") or []
        ]
        if continuation is not None
        else []
    )
    deferred_qty = sum(residual_quantities)
    conserved_total = immediate_qty + deferred_qty
    if any(_positive_int(item.get("qty")) <= 0 for item in orders):
        blockers.append("nonpositive_leg_qty")
    if len(orders) > immediate_qty:
        blockers.append("leg_count_exceeds_immediate_qty")
    if deferred_qty and any(value <= 0 for value in residual_quantities):
        blockers.append("nonpositive_residual_leg_qty")
    if (
        continuation is not None
        and _positive_int(continuation.get("requested_qty")) != expected_total_qty
    ):
        blockers.append("probe_continuation_requested_qty_mismatch")
    if conserved_total != expected_total_qty:
        blockers.append("quantity_conservation_failed")

    price_plan: list[dict[str, Any]] = []
    legs: list[dict[str, Any]] = []
    decorated_orders: list[dict[str, Any]] = []
    for index, order in enumerate(orders, start=1):
        price = _positive_int(order.get("price"))
        order_type = str(
            order.get("order_type_code") or order.get("order_type") or "00"
        ).strip()
        if price <= 0 and order_type not in {"3", "03"}:
            blockers.append(f"leg_{index}_numeric_price_missing")
        candidate_id = _price_candidate_id(order, index)
        price_plan.append(
            {
                "price_candidate_id": candidate_id,
                "numeric_price": price,
                "order_type_code": order_type,
                "source": PRICE_OWNER,
            }
        )
        legs.append(
            {
                "leg_index": index,
                "qty": _positive_int(order.get("qty")),
                "price_candidate_id": candidate_id,
                "numeric_price": price,
                "execution_phase": "immediate",
            }
        )
        decorated_orders.append({**order, "price_candidate_id": candidate_id})
    for residual_index, residual_qty in enumerate(residual_quantities, start=1):
        candidate_id = f"probe_residual_resolver:leg{residual_index + 1}"
        legs.append(
            {
                "leg_index": len(orders) + residual_index,
                "qty": residual_qty,
                "price_candidate_id": candidate_id,
                "numeric_price": None,
                "execution_phase": "after_verified_probe_fill",
            }
        )
        price_plan.append(
            {
                "price_candidate_id": candidate_id,
                "numeric_price": None,
                "order_type_code": "00",
                "source": "probe_fill_price_resolver",
            }
        )
    if len(legs) > expected_total_qty:
        blockers.append("leg_count_exceeds_total_qty")

    plan_core = {
        "schema_version": SCHEMA_VERSION,
        "price_schema_version": PRICE_SCHEMA_VERSION,
        "stage": "entry",
        "action_receipt_id": action_receipt_id,
        "action_owner": action_owner,
        "quantity_policy_owner": QUANTITY_OWNER,
        "quantity_policy_version": str(quantity_policy_version or "baseline_current"),
        "split_policy_version": str(split_policy_version or "baseline_current"),
        "price_policy_owner": PRICE_OWNER,
        "execution_sizing_policy": POLICY_VERSION,
        "migration_baseline": True,
        "total_qty": expected_total_qty,
        "immediate_qty": immediate_qty,
        "deferred_probe_residual_qty": deferred_qty,
        "leg_count": len(legs),
        "legs": legs,
        "price_candidates": price_plan,
        "quantity_conservation_holds": conserved_total == expected_total_qty,
        "quantity_increase_forbidden": True,
        "action_authority_forbidden": True,
        "valid": not blockers,
        "blockers": blockers,
    }
    plan_id = f"entry-sizing-{_content_sha256(plan_core)[:24]}"
    common_fields = {
        "entry_execution_sizing_plan_schema": SCHEMA_VERSION,
        "entry_execution_sizing_plan_id": plan_id,
        "entry_execution_sizing_policy": POLICY_VERSION,
        "entry_execution_sizing_action_receipt_id": action_receipt_id or "-",
        "entry_execution_sizing_quantity_policy_version": plan_core[
            "quantity_policy_version"
        ],
        "entry_execution_sizing_split_policy_version": plan_core[
            "split_policy_version"
        ],
        "entry_execution_sizing_total_qty": expected_total_qty,
        "entry_execution_sizing_immediate_qty": immediate_qty,
        "entry_execution_sizing_deferred_qty": deferred_qty,
        "entry_execution_sizing_leg_count": plan_core["leg_count"],
        "entry_execution_sizing_quantity_conservation_holds": plan_core[
            "quantity_conservation_holds"
        ],
        "entry_execution_sizing_quantity_increase_forbidden": True,
        "entry_execution_sizing_migration_baseline": True,
        "entry_execution_sizing_plan_emitted": True,
        "entry_execution_sizing_valid": not blockers,
        "entry_execution_sizing_blockers": blockers,
        "entry_execution_sizing_plan_sha256": _content_sha256(plan_core),
    }
    decorated_orders = [{**item, **common_fields} for item in decorated_orders]
    if continuation is not None and decorated_orders:
        continuation_common = dict(continuation.get("common_fields") or {})
        continuation["common_fields"] = {**continuation_common, **common_fields}
        decorated_orders[0]["entry_split_order_probe_continuation"] = continuation
    return decorated_orders, {**common_fields, "entry_execution_sizing_plan": plan_core}
