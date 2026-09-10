"""Frozen original-owner pending BUY census, separate from alpha/target lots.

Late fills belong to whole-exit residual quantities. They never amend the
frozen TargetGroup, first-fill clocks, decision policy or economic denominator.
"""

from copy import deepcopy

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from .group_terminal import IDENTITY
from .reducer import OrderKey
from .target_group import _digest

FIELDS = tuple(k for k in IDENTITY if k != "filled_qty")


def capture_pending_buys(session, orders, registry, entry_signal_id):
    if not isinstance(orders, list) or not all(isinstance(o, dict) for o in orders):
        raise ValueError("whole_exit_pending_buy_ordinary_orders_invalid")
    original = {order for _, order, _, _, _ in session.group.lots}
    captured = []
    for order in orders:
        if (
            order.get("side") != "BUY"
            or order.get("owner_position_id") != session.context.position_id
        ):
            continue
        key = OrderKey(order.get("order_date"), order.get("order_no"))
        if key in original:
            continue
        row = registry.assert_owner(
            context=session.context,
            order_date=key.trading_date,
            broker_order_no=key.order_no,
        )
        if (
            order.get("order_role") not in {"ENTRY_BUY", "SCALE_IN_BUY"}
            or order.get("parent_entry_signal_id") != entry_signal_id
            or order.get("broker_accepted") is not True
            or order.get("owner_id") != session.context.owner_id
            or order.get("owner_registry_intent_id") != row.get("intent_id")
            or order.get("owner_client_intent_id") != row.get("client_intent_id")
            or order.get("route") != session.group.scope.route
            or type(order.get("requested_qty")) is not int
            or order["requested_qty"] != row.get("quantity")
            or type(order.get("filled_qty")) is not int
            or not 0
            <= order["filled_qty"]
            <= row.get("filled_qty", -1)
            <= row["quantity"]
            or order.get("status") != "SUBMITTED"
            or row.get("state") not in {"ORDER_BOUND", "ORDER_TERMINAL"}
            or row.get("canceled_qty", 0) != 0
        ):
            raise ValueError("whole_exit_pending_buy_original_binding_invalid")
        captured.append(
            {
                "identity": {k: row[k] for k in FIELDS},
                "initial_filled_qty": row["filled_qty"],
                "initial_ordinary_filled_qty": order["filled_qty"],
                "ordinary_sha256": canonical_sha256(order),
                "registry_event_hash": row["event_hash"],
            }
        )
    validate_pending_buys(captured, session, registry=registry, orders=orders)
    return deepcopy(captured)


def validate_pending_buys(captured, session, *, registry=None, orders=None):
    if not isinstance(captured, list):
        raise ValueError("whole_exit_pending_buy_census_invalid")
    seen = set()
    original = {order for _, order, _, _, _ in session.group.lots}
    for record in captured:
        if not isinstance(record, dict) or set(record) != {
            "identity",
            "initial_filled_qty",
            "initial_ordinary_filled_qty",
            "ordinary_sha256",
            "registry_event_hash",
        }:
            raise ValueError("whole_exit_pending_buy_record_invalid")
        identity = record["identity"]
        if not isinstance(identity, dict) or set(identity) != set(FIELDS):
            raise ValueError("whole_exit_pending_buy_identity_invalid")
        key = OrderKey(identity["order_date"], identity["broker_order_no"])
        if (
            key in seen
            or key in original
            or key == session.group.target
            or key.trading_date != session.group.target.trading_date
            or not isinstance(key.order_no, str)
            or len(key.order_no) != 7
            or not key.order_no.isascii()
            or not key.order_no.isdigit()
            or int(key.order_no) == 0
            or identity["side"] != "BUY"
            or identity["action"] != "NEW"
            or identity["symbol"] != session.group.scope.symbol
            or identity["route"] != session.group.scope.route
            or any(
                identity[k] != getattr(session.context, k)
                for k in ("owner_type", "owner_id", "position_id")
            )
            or type(identity["quantity"]) is not int
            or identity["quantity"] <= 0
            or type(record["initial_filled_qty"]) is not int
            or type(record["initial_ordinary_filled_qty"]) is not int
            or not 0
            <= record["initial_ordinary_filled_qty"]
            <= record["initial_filled_qty"]
            <= identity["quantity"]
            or not _digest(record["ordinary_sha256"])
            or not _digest(record["registry_event_hash"])
            or not all(
                isinstance(identity[k], str) and identity[k]
                for k in ("account_key", "intent_id", "client_intent_id")
            )
        ):
            raise ValueError("whole_exit_pending_buy_scope_invalid")
        seen.add(key)
        if registry is not None:
            row = registry.assert_owner(
                context=session.context,
                order_date=key.trading_date,
                broker_order_no=key.order_no,
            )
            if (
                any(row.get(k) != v for k, v in identity.items())
                or type(row.get("filled_qty")) is not int
                or not record["initial_filled_qty"]
                <= row["filled_qty"]
                <= row["quantity"]
            ):
                raise ValueError("whole_exit_pending_buy_registry_changed")
        if orders is not None:
            matches = [
                o
                for o in orders
                if o.get("order_date") == key.trading_date
                and o.get("order_no") == key.order_no
            ]
            if (
                len(matches) != 1
                or canonical_sha256(matches[0]) != record["ordinary_sha256"]
            ):
                raise ValueError("whole_exit_pending_buy_ordinary_generation_changed")
    return seen
