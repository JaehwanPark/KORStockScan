"""Exact group quantity closure across bounded runners, under the owner lock.

No order submission, implicit lot SELL attribution, profit or new BUY authority.
The original target and runner must both be terminal; a canceled remainder is
still inventory. Unknown/unbound intents cannot be hidden by a zero net balance.
Every separately submitted TTL cancel requires its own terminal proof.
"""

from copy import deepcopy

from src.trading.config.machine_adaptive_exit_policy import canonical_sha256
from .reducer import OrderKey
from .target_group import _digest

SCHEMA = "machine_adaptive_exit_group_terminal_v1"
ROLE = "GROUP_TERMINAL"
IDENTITY = (
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


def _terminal_order(row, role):
    proof = row.get("terminal_reconciliation")
    if (
        row.get("state") != "ORDER_TERMINAL"
        or row.get("side") != "SELL"
        or row.get("action") != "NEW"
        or type(row.get("quantity")) is not int
        or row["quantity"] <= 0
        or type(row.get("filled_qty")) is not int
        or not 0 <= row["filled_qty"] <= row["quantity"]
        or not isinstance(proof, dict)
        or type(proof.get("quantity")) is not int
        or type(proof.get("filled_qty")) is not int
        or proof.get("schema") != "order_owner_terminal_reconciliation_v1"
        or proof.get("source_contract") != "machine_adaptive_exit_dated_current_v1"
        or any(proof.get(k) != row.get(k) for k in IDENTITY)
        or not _digest(proof.get("receipt_sha256"))
    ):
        raise ValueError("group_terminal_exact_sell_proof_required")
    return {
        "trading_date": row["order_date"],
        "order_no": row["broker_order_no"],
        "intent_id": row["intent_id"],
        "client_intent_id": row["client_intent_id"],
        "role": role,
        "route": row["route"],
        "requested_qty": row["quantity"],
        "filled_qty": row["filled_qty"],
        "remaining_qty": 0,
        "unfilled_terminal_qty": row["quantity"] - row["filled_qty"],
        "reconciliation_sha256": proof["receipt_sha256"],
        "fill_amount_krw": None,
        "commission_krw": None,
        "tax_krw": None,
    }


def _runner_cancel_proof(runner, ttl):
    """Shared successor-admission/terminal contract, not cancellation by ACK."""
    proof = ttl.get("terminal_cancel_reconciliation")
    if (
        ttl.get("state") != "ORDER_TERMINAL"
        or ttl.get("side") != "SELL"
        or ttl.get("action") != "CANCEL"
        or type(ttl.get("filled_qty")) is not int
        or ttl["filled_qty"] != 0
        or not isinstance(proof, dict)
        or runner.get("terminal_cancel_reconciliation") != proof
        or any(
            type(proof.get(k)) is not int
            for k in ("requested_qty", "filled_qty", "remaining_qty", "confirmed_qty")
        )
        or any(
            proof.get(k) != v
            for k, v in {
                "schema": "order_owner_terminal_cancel_reconciliation_v1",
                "source_contract": "machine_adaptive_exit_terminal_cancel_dated_current_v1",
                "target_intent_id": runner["intent_id"],
                "cancel_intent_id": ttl["intent_id"],
                "target_order_no": runner["broker_order_no"],
                "cancel_order_no": ttl["broker_order_no"],
                "order_date": runner["order_date"],
                "requested_qty": ttl["quantity"],
                "filled_qty": runner["filled_qty"],
                "remaining_qty": 0,
            }.items()
        )
        or type(proof.get("confirmed_qty")) is not int
        or not 0 < proof["confirmed_qty"] <= ttl["quantity"]
        or runner.get("canceled_qty") != proof["confirmed_qty"]
        or runner["quantity"] != runner["filled_qty"] + proof["confirmed_qty"]
        or not _digest(proof.get("receipt_sha256"))
    ):
        raise ValueError("group_terminal_ttl_cancel_recovery_required")
    return deepcopy(proof)


def _rows(executor):
    """Require an exact complete position census, not just known order IDs."""
    executor._authorize()
    c = executor.coordinator
    state, target = c._read(), c._target()
    if state is None or state["target_intent_id"] != target["intent_id"]:
        raise ValueError("group_terminal_frozen_target_required")
    buys = [c._row(order) for _, order, _, _, _ in c.group.lots]
    if any(
        row["state"] != "ORDER_TERMINAL"
        or type(row.get("quantity")) is not int
        or type(row.get("filled_qty")) is not int
        for row in buys
    ):
        raise ValueError("group_terminal_buy_terminal_required")
    records, intents = executor.action_records(), {}
    for kind, record in records.items():
        intent = executor._intent(record)
        if intent is None or intent["state"] not in {"ORDER_BOUND", "ORDER_TERMINAL"}:
            raise ValueError("group_terminal_unresolved_action")
        intents[kind] = intent
    if "SELL_RUNNER" in intents and "RELEASE_RUNNER" not in intents:
        raise ValueError("group_terminal_release_lineage_missing")
    expected = buys + [target] + list(intents.values())
    census = c.adapter.registry.position_intents(
        context=c.adapter.context, symbol=c.group.scope.symbol
    )
    # Include terminal and unbound rows too; never accept netting with another
    # generation, side, route or owner. Owner guard supplies broker/custody checks.
    if len({r["intent_id"] for r in expected}) != len(expected) or {
        r["intent_id"]: r for r in census
    } != {r["intent_id"]: r for r in expected}:
        raise ValueError("group_terminal_position_census_conflict")
    return state, target, buys, records, intents


def _build(executor, observed_at_ms):
    c = executor.coordinator
    state, target, buys, records, intents = _rows(executor)
    orders = [_terminal_order(target, "original_target")]
    for kind, row in intents.items():
        if records[kind]["action"]["kind"] == "SELL_RUNNER":
            orders.append(_terminal_order(row, "adaptive_runner"))
    cancel_proofs = []
    cancel = intents.get("RELEASE_RUNNER")
    if cancel is not None:
        proof = cancel.get("cancel_reconciliation")
        if (
            state["phase"] != "RELEASE_RECONCILED"
            or state["cancel_order"]
            != {
                "trading_date": cancel["order_date"],
                "order_no": cancel["broker_order_no"],
            }
            or cancel.get("state") != "ORDER_TERMINAL"
            or type(cancel.get("filled_qty")) is not int
            or cancel["filled_qty"] != 0
            or not isinstance(proof, dict)
            or target.get("partial_cancel_reconciliation") != proof
            or any(
                proof.get(k) != v
                for k, v in {
                    "schema": "order_owner_partial_cancel_reconciliation_v1",
                    "source_contract": "machine_adaptive_exit_full_cancel_request_dated_current_v1",
                    "target_intent_id": target["intent_id"],
                    "cancel_intent_id": cancel["intent_id"],
                    "target_order_no": target["broker_order_no"],
                    "cancel_order_no": cancel["broker_order_no"],
                    "order_date": target["order_date"],
                    "confirmed_qty": state["requested_qty"],
                }.items()
            )
            or not _digest(proof.get("receipt_sha256"))
            or canonical_sha256(proof) != state["release"]["cancel_proof_hash"]
            or target.get("canceled_qty") != state["requested_qty"]
        ):
            raise ValueError("group_terminal_partial_cancel_proof_required")
        cancel_proofs.append(deepcopy(proof))
    elif target.get("canceled_qty", 0) != 0:
        raise ValueError("group_terminal_unowned_cancel")
    # A runner terminal never proves its separately sent TTL cancel terminal.
    for kind, ttl in intents.items():
        if records[kind]["action"]["kind"] == "CANCEL_RUNNER_TTL":
            runner = intents[kind.replace("CANCEL_RUNNER_TTL", "SELL_RUNNER")]
            cancel_proofs.append(_runner_cancel_proof(runner, ttl))
    sell_qty = sum(row["filled_qty"] for row in orders)
    if sell_qty != c.group.quantity:
        raise ValueError("group_terminal_owned_residual_requires_recovery")
    if (
        c.adapter.registry.owner_position_qty(
            c.adapter.context.position_id, symbol=c.group.scope.symbol
        )
        != 0
    ):
        raise ValueError("group_terminal_position_not_flat")
    if (
        type(observed_at_ms) is not int
        or not state["frozen_at_ms"] <= observed_at_ms <= c.adapter.now_ms()
    ):
        raise ValueError("group_terminal_observation_time_invalid")
    payload = {
        "schema": SCHEMA,
        "terminal_id": executor.binding_hash,
        "group_binding_hash": c.binding_hash,
        "group_hash": c.allocation.group_hash,
        "coordinator_state_hash": state["canonical_sha256"],
        "action_hashes": {k: r["canonical_sha256"] for k, r in records.items()},
        "scope_key": c.group.scope.key,
        "episode_id": c.group.episode_id,
        "owner_type": c.adapter.context.owner_type,
        "owner_id": c.adapter.context.owner_id,
        "position_id": c.adapter.context.position_id,
        "observed_at_ms": observed_at_ms,
        "execution_status": "reconciled_flat",
        "buy_filled_qty": c.group.quantity,
        "sell_filled_qty": sell_qty,
        "buy_orders": [{k: r[k] for k in IDENTITY} for r in buys],
        "orders": orders,
        "cancel_proofs": cancel_proofs,
        "actual_lot_fill_attribution": None,
        "realized_pnl_status": "unreconciled_exact_fill_cost_required",
        "realized_net_profit_krw": None,
        "economic_acceptance": False,
        "new_entry_authority": False,
    }
    return payload | {"canonical_sha256": canonical_sha256(payload)}


def validate_group_terminal(receipt, executor):
    """Recompute against the original registry; a self-hash is not authority."""
    if not isinstance(receipt, dict):
        raise ValueError("group_terminal_receipt_missing")
    expected = _build(executor, receipt.get("observed_at_ms"))
    if receipt != expected:
        raise ValueError("group_terminal_receipt_binding_conflict")


def reconcile_group_terminal(executor):
    """Bounded read-only broker reconciliation then durable quantity receipt.

    Registry reconciliation writes and the owner's atomic terminal save are the
    only mutations. Caller decides when to poll; no retry/sleep/scheduled worker.
    Completion is not ordinary episode archival or permission for another BUY.
    """
    c = executor.coordinator
    _, target, _, _, intents = _rows(executor)
    key = executor._key(ROLE)
    old = deepcopy(c.load_record(key))
    if old is not None:
        validate_group_terminal(old, executor)
        return {"status": "group_terminal", "group_terminal": True, "receipt": old}
    start = c.adapter.now_ms()
    runners = [row for kind, row in intents.items() if kind.startswith("SELL_RUNNER")]
    # Earlier generations already required independent root/child terminal
    # proofs before their successor could be admitted. Revalidate those local
    # proofs through _rows/_build; do not multiply identical broker queries or
    # silently exceed the original bounded two-order observation window.
    rows = [target] + runners[-1:]
    for row in rows:
        executor._authorize()
        order = OrderKey(row["order_date"], row["broker_order_no"])
        snapshot = c.adapter.reconcile_owned_sell(order)
        now = c.adapter.now_ms()
        executor._authorize()
        if (
            snapshot.source_ok is not True
            or snapshot.order != order
            or not _digest(snapshot.receipt_hash)
            or not 0 <= now - start <= c.max_age
            or not start <= snapshot.observed_at_ms <= now
            or type(snapshot.filled_qty) is not int
            or not 0 <= snapshot.filled_qty <= row["quantity"]
            or type(snapshot.remaining_qty) is not int
            or not 0 <= snapshot.remaining_qty <= row["quantity"] - snapshot.filled_qty
            or snapshot.terminal is not (snapshot.remaining_qty == 0)
        ):
            return {"status": "group_terminal_source_gap", "group_terminal": False}
        if not snapshot.terminal:
            return {"status": "group_orders_working", "group_terminal": False}
    candidate = _build(executor, c.adapter.now_ms())
    executor._authorize()
    if not 0 <= c.adapter.now_ms() - start <= c.max_age:
        return {"status": "group_terminal_source_gap", "group_terminal": False}
    if c.load_record(key) is not None:
        raise ValueError("group_terminal_generation_changed")
    c.save_record(key, None, deepcopy(candidate))
    executor._authorize()
    saved = deepcopy(c.load_record(key))
    if saved != candidate:
        raise ValueError("group_terminal_durable_save_missing")
    validate_group_terminal(saved, executor)
    return {"status": "group_terminal", "group_terminal": True, "receipt": saved}
