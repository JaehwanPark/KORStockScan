"""One-tick amendments from the original locked owner, OFF without its pin.

Fresh WS-derived trade-backed pressure triggers the original owner directly,
with no Holding AI call or wait. Only the durable AMEND phase claims reconciliation;
no cancel/new fallback or strategy-level ratchet count limit is allowed.
"""

from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
import hashlib
import os
import time

from src.trading.config.machine_target_ratchet_policy import (
    load_policy,
    FAMILY,
    PATH_ENV,
    HASH_ENV,
)
from src.trading.order.adaptive_exit.reducer import OrderKey
from src.trading.order.owner_custody_registry import OwnerRegistryError
from src.trading.order.tick_utils import move_price_by_ticks
from src.trading.order.target_amend import reconcile_amendment
from src.trading.market.target_pressure import evaluate_pressure
from src.trading.market.micro_confirmation import _live_snapshot_path

KEY = "holding_target_amendment"


def drive(
    owner, container, binding, context, now, *, allowed, project, probe_only=False
):
    """True claims this target; durable pending state is recovered even OFF."""
    from src.trading.order import profit_stagnation_owners as original

    pending = container.get(KEY)
    if probe_only and KEY in container:
        return False  # Recovery keeps its existing bounded owner cadence.
    if KEY in container and not isinstance(pending, dict):
        raise ValueError("ratchet_claim_invalid")
    if getattr(owner, "_profit_exit_reload_required", False):
        raise OSError("ratchet_owner_reload_required")
    if getattr(owner, "profit_exit_lock_held", lambda: False)() is not True:
        return KEY in container

    def save():
        original._save_initial(owner)

    try:
        selected = load_policy(
            now=now, owner=binding["owner"], entered_at=binding["entered_at"]
        )
    except (ValueError, TypeError, KeyError, OSError, AttributeError) as exc:
        selected = None
        if not probe_only:
            container["holding_target_status"] = "policy_invalid:" + type(exc).__name__
    if not pending and (not selected or not allowed()):
        return False
    if (
        type(binding.get("quantity")) is not int
        or binding["quantity"] <= 0
        or type(binding.get("price")) is not int
        or binding["price"] <= 0
        or type(binding.get("entry_price")) not in {int, float}
        or not Decimal(str(binding["entry_price"])).is_finite()
        or binding["entry_price"] <= 0
    ):
        raise ValueError("ratchet_owned_position_invalid")
    if pending:
        if pending.get("binding") != binding:
            raise ValueError("ratchet_frozen_target_binding_changed")
        policy, pin = pending["policy"], pending["pin"]
    else:
        policy, pin = selected
    args = dict(
        registry=owner.owner_registry,
        context=context,
        policy_hash=pin,
        write_guard=lambda _: False,
        authority_policy_id=FAMILY,
    )
    if binding["owner"] == "widget_auto_trade":
        args["code"] = binding["symbol"]
    adapter = owner.gateway.adaptive_exit_adapter(**args)
    target = OrderKey(binding["date"], binding["order_no"])

    def current_time():
        return datetime.fromtimestamp(adapter.now_ms() / 1000, now.tzinfo)

    def fresh_signal():
        return evaluate_pressure(
            symbol=binding["symbol"],
            route=binding["route"],
            quantity=binding["quantity"],
            target_price=binding["price"],
            now=current_time(),
        )

    def quote_allows(q):
        bid, entry = (
            Decimal(str(q["executable_bid"])),
            Decimal(str(binding["entry_price"])),
        )
        return bid >= binding["price"] and bid * (
            1 - Decimal(str(policy["slippage_bps"])) / 10000
        ) > entry * (1 + Decimal(str(policy["round_trip_cost_pct"])) / 100)

    try:
        if not pending:
            owned = adapter._owned(target)
            if owned.get("filled_qty", 0) or owned.get(
                "amendment_parent_filled_qty", 0
            ):
                return False
            signal = fresh_signal()
            if probe_only:
                return signal["decision"] == "RAISE_ONE_TICK" and quote_allows(
                    signal["quote"]
                )
            if not quote_allows(signal["quote"]):
                signal = dict(
                    signal,
                    decision="KEEP_TARGET",
                    reasons=signal["reasons"] + ["target_or_net_edge_guard"],
                )
            container["holding_target_last_decision"] = deepcopy(signal)
            quote = signal["quote"]
            if signal["decision"] != "RAISE_ONE_TICK" or not quote_allows(quote):
                container["holding_target_status"] = "pressure_keep_original_target"
                return False
            # The adapter performs the single mandatory broker preflight.
            # Do not duplicate it here or wait for a Provider decision.
            action = (
                "target-amend:"
                + hashlib.sha256(
                    f"{context.position_id}:{binding['date']}:{binding['order_no']}:{pin}".encode()
                ).hexdigest()
            )
            pending = dict(
                binding=deepcopy(binding),
                policy=deepcopy(policy),
                pin=pin,
                action=action,
                price=move_price_by_ticks(binding["price"], 1),
                trigger="ws_executable_target_reached",
                trigger_observed_at=current_time().isoformat(),
                quote=deepcopy(quote),
                pressure=deepcopy(signal),
            )
            container[KEY] = pending
            save()  # Restart must see a claim before any reservation or write.

            def write_guard(request):
                permitted = bool(
                    allowed()
                    and request.action == "AMEND"
                    and request.predecessor == target
                    and request.quantity == binding["quantity"]
                    and request.limit_price == pending["price"]
                    and load_policy(
                        now=current_time(),
                        owner=binding["owner"],
                        entered_at=binding["entered_at"],
                    )
                    == (policy, pin)
                )
                if not permitted:
                    return False
                latest = fresh_signal()
                # Recompute after broker preflight and durable reservation;
                # a pressure change cannot reuse the earlier raise decision.
                pending["prewrite_pressure"] = deepcopy(latest)
                return latest["decision"] == "RAISE_ONE_TICK" and quote_allows(
                    latest["quote"]
                )

            adapter.write_guard = write_guard
            adapter.amend_owned_sell(
                target,
                quantity=binding["quantity"],
                limit_price=pending["price"],
                action_id=action,
            )
        intent = adapter.registry.intent_for_client(
            context=replace(context, client_intent_id=pending["action"])
        )
        if intent is None:
            # The claim was fsynced but no reservation/write happened. Do not
            # retry this saved trigger; release to the original target owner.
            container["holding_target_status"] = "no_write_reserved"
            container.pop(KEY)
            save()
            return False
        if intent["state"] == "INTENT_REJECTED":
            container["holding_target_status"] = "amend_rejected_original_retained"
            container.pop(KEY)
            container["holding_target_disabled_order"] = binding["order_no"]
            save()
            return False
        child = reconcile_amendment(adapter, intent, price=pending["price"])
        project(child, pending)
        container.setdefault("holding_target_history", []).append(deepcopy(pending))
        container.pop(KEY)
        container["holding_target_status"] = "amendment_reconciled"
        save()
        return True
    except (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        IndexError,
        OverflowError,
        PermissionError,
        OwnerRegistryError,
    ) as exc:
        if probe_only:
            return False
        if getattr(owner, "_profit_exit_reload_required", False):
            raise
        container["holding_target_status"] = str(exc)
        if KEY not in container:
            container["holding_target_last_decision"] = dict(
                decision="KEEP_TARGET",
                source_quality_status="source_gap",
                reasons=[str(exc)],
                observed_at=current_time().isoformat(),
            )
        if KEY in container:
            save()
        return KEY in container


def episode(machine, leg, now, *, probe_only=False):
    if KEY not in leg and not (os.getenv(PATH_ENV) or os.getenv(HASH_ENV)):
        return False
    from src.trading.order import profit_stagnation_owners as original

    prior = leg.get(original.KEY)
    if KEY not in leg and (
        leg.get("status") != "TARGET_OPEN"
        or leg.get("target_filled_qty", 0)
        or leg.get("holding_target_disabled_order") == leg.get("target_order_no")
        or (
            prior
            and (
                prior.get("phase") != "TARGET"
                or prior.get("orders")
                or prior.get("cancel_id")
            )
        )
    ):
        return False
    context = machine._episode_owner_context(
        leg=leg, action="holding_target", ordinal=1
    )
    binding = dict(
        owner="episode",
        symbol=machine.policy.symbol,
        position_id=context.position_id,
        date=leg["target_order_date"],
        order_no=leg["target_order_no"],
        price=leg["target_price"],
        quantity=leg["target_quantity"],
        route=machine.owner_registry.assert_owner(
            context=context,
            order_date=leg["target_order_date"],
            broker_order_no=leg["target_order_no"],
        )["route"],
        entry_price=leg["fill_price"],
        entered_at=(machine._state.get("signal_features") or {}).get(
            "signal_decision_at", ""
        ),
    )

    def allowed():
        return (
            original.guard(
                machine, symbol=binding["symbol"], owner_type="episode", now=now
            )
            and machine._state.get("status") != "BLOCKED"
            and not machine._state.get("owner_registry_reconciliation_required")
            and not any(
                v
                for item in machine._state.get("legs", [])
                for k, v in item.items()
                if k.endswith("owner_registry_reconciliation_required")
            )
        )

    def project(child, pending):
        if child["amendment_parent_filled_qty"]:
            # No invented blended fill price or silent quantity resize.
            raise ValueError(
                "amendment_race_partial_fill_requires_exact_episode_recovery"
            )
        leg.update(
            target_order_no=child["broker_order_no"],
            target_owner_registry_intent_id=child["intent_id"],
            target_price=pending["price"],
            target_filled_qty=child["filled_qty"],
            position_qty=leg["buy_filled_qty"] - child["filled_qty"],
            target_fill_price=0,
            status=(
                "COMPLETE"
                if child["filled_qty"] == child["quantity"]
                else "TARGET_OPEN"
            ),
        )
        leg.pop(original.KEY, None)
        machine._own_order(child["broker_order_no"])
        machine._sync_aggregate()

    return drive(
        machine,
        leg,
        binding,
        context,
        now,
        allowed=allowed,
        project=project,
        probe_only=probe_only,
    )


def widget(trader, state, now, *, allow_new=False, probe_only=False):
    if KEY not in state and not (os.getenv(PATH_ENV) or os.getenv(HASH_ENV)):
        return False
    from src.trading.order import profit_stagnation_owners as original

    if original.KEY in state:
        return False
    pending = state.get(KEY)
    if not pending and not allow_new:
        return False  # Missing source cannot prove original final EXIT absent.
    targets = [
        o
        for o in state.get("orders", [])
        if o.get("side") == "SELL"
        and o.get("order_role") == "TAKE_PROFIT_SELL"
        and o.get("broker_accepted") is True
        and o.get("status") == "SUBMITTED"
        and o.get("filled_qty") == 0
        and o.get("parent_entry_signal_id") == state.get("entry_signal_id")
        and state.get("holding_target_disabled_order") != o.get("order_no")
    ]
    if pending:
        targets = [
            o
            for o in state["orders"]
            if o.get("order_no") == pending["binding"]["order_no"]
            and o.get("order_date") == pending["binding"]["date"]
        ]
    buys = original.widget_position_buys(state)
    if not targets or not buys:
        return bool(pending)
    if not pending and (
        state.get("exit_requested")
        or any(
            o.get("status") not in {"FILLED", "PARTIAL_CANCELED"}
            or not o.get("filled_qty")
            or not o.get("fill_price")
            for o in buys
        )
    ):
        return False
    for order in targets:
        context = trader._owner_context_from_order(order)
        binding = (
            pending["binding"]
            if pending
            else dict(
                owner="widget_auto_trade",
                symbol=state["code"],
                position_id=context.position_id,
                date=order["order_date"],
                order_no=order["order_no"],
                price=order["limit_price"],
                quantity=order["requested_qty"],
                route=trader.owner_registry.assert_owner(
                    context=context,
                    order_date=order["order_date"],
                    broker_order_no=order["order_no"],
                )["route"],
                entry_price=sum(o["fill_price"] * o["filled_qty"] for o in buys)
                / sum(o["filled_qty"] for o in buys),
                entered_at=min(o.get("intent_created_at", "") for o in buys),
            )
        )

        def allowed():
            return (
                not state.get("exit_requested")
                and not state.get("owner_registry_reconciliation_required")
                and not any(
                    v
                    for o in state.get("orders", [])
                    for k, v in o.items()
                    if k.endswith("owner_registry_reconciliation_required")
                )
                and not any(
                    o.get("side") == "BUY"
                    and not original.widget_buy_proven_not_sent(o)
                    and o.get("status")
                    not in {
                        "FILLED",
                        "CANCELED",
                        "PARTIAL_CANCELED",
                        "TERMINAL_UNFILLED",
                        "REJECTED",
                    }
                    for o in state.get("orders", [])
                )
                and original.guard(
                    trader,
                    symbol=state["code"],
                    owner_type="widget_auto_trade",
                    now=now,
                )
            )

        def project(child, claim):
            successor = deepcopy(order)
            for field in list(successor):
                if "cancel" in field:
                    successor.pop(field)
            successor.update(
                order_no=child["broker_order_no"],
                requested_qty=child["quantity"],
                owner_registry_intent_id=child["intent_id"],
                owner_client_intent_id=child["client_intent_id"],
                limit_price=claim["price"],
                filled_qty=child["filled_qty"],
                remaining_qty=child["quantity"] - child["filled_qty"],
                fill_price=None,
                fill_amount_krw=None,
                commission_krw=None,
                tax_krw=None,
                status=(
                    "FILLED"
                    if child["quantity"] == child["filled_qty"]
                    else "SUBMITTED"
                ),
            )
            order.update(
                filled_qty=child["amendment_parent_filled_qty"],
                remaining_qty=0,
                status=(
                    "PARTIAL_CANCELED"
                    if child["amendment_parent_filled_qty"]
                    else "CANCELED"
                ),
                fill_price=None,
                fill_amount_krw=None,
                commission_krw=None,
                tax_krw=None,
            )
            state["orders"].append(successor)
            state.pop(original.OBSERVATION_KEY, None)

        if drive(
            trader,
            state,
            binding,
            context,
            now,
            allowed=allowed,
            project=project,
            probe_only=probe_only,
        ):
            return True
    return False


def wait_for_pressure(owner, delay, *, owner_type, now_fn):
    """Shorten sleep only on a new, eligible WS snapshot; never submit here.

    A local 50ms stat watcher avoids a second broker writer and does not speed
    up reconciliation on neutral/missing input. The awakened original loop
    still reloads source EXIT, ownership and all write guards. Publisher
    batching and broker preflight latency remain; this is not a raw callback.
    """
    if not (os.getenv(PATH_ENV) and os.getenv(HASH_ENV)):
        time.sleep(delay)
        return
    deadline = time.monotonic() + delay
    path = _live_snapshot_path()

    def signature():
        try:
            stat = path.stat()
            return stat.st_ino, stat.st_mtime_ns, stat.st_size
        except OSError:
            return None

    previous = signature()
    while (remaining := deadline - time.monotonic()) > 0:
        time.sleep(min(0.05, remaining))
        current = signature()
        if current is None or current == previous:
            continue
        previous = current
        try:
            now = now_fn()
            if owner_type == "episode":
                ready = any(
                    episode(owner, leg, now, probe_only=True)
                    for leg in owner._state.get("legs", [])
                )
            else:
                # This is a wake hint, not proof that final EXIT is absent.
                ready = any(
                    widget(owner, state, now, allow_new=True, probe_only=True)
                    for state in owner._state.get("symbols", {}).values()
                )
            if ready:
                return
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            IndexError,
            OverflowError,
            OSError,
            PermissionError,
            OwnerRegistryError,
        ):
            # Original scheduled evaluation retains diagnostics/recovery.
            continue
